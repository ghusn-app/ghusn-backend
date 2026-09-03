import os
import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.user import User, UserRole
from app.models.farmer import Farmer
from app.models.refresh_token import RefreshToken
from app.security import hash_password, verify_password, create_access_token, create_refresh_token, create_email_verification_token, decode_email_verification_token,create_password_reset_token,decode_password_reset_token
from app.services.email_service import send_password_reset_link, send_signup_verification_link
from app.schemas.user import (
    UserSignup, UserLogin, TokenPair, RefreshRequest, GoogleAuthRequest,
    ForgotPasswordRequest, VerifyResetCodeRequest, ResetPasswordRequest,
    VerifySignupRequest,
)

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

router = APIRouter(prefix="/auth", tags=["Auth"])


def _issue_token_pair(user: User, db: Session) -> TokenPair:
    access_token = create_access_token({"user_id": user.user_id, "role": user.role.value})

    refresh_token_value, refresh_expires_at = create_refresh_token()
    new_refresh = RefreshToken(
        token=refresh_token_value,
        user_id=user.user_id,
        expires_at=refresh_expires_at,
    )
    db.add(new_refresh)
    db.commit()

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token_value,
        refresh_token_expires_at=refresh_expires_at,
    )


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="البريد الإلكتروني مستخدم مسبقاً")

    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=UserRole.FARMER,
        is_verified=True,
    )
    db.add(new_user)
    db.flush()

    new_farmer = Farmer(user_id=new_user.user_id)
    db.add(new_farmer)
    db.commit()
    db.refresh(new_user)

    verification_token = create_email_verification_token(new_user.user_id)
    send_signup_verification_link(new_user.email, verification_token)

    return {"message": "تم إنشاء الحساب. تحققي من بريدك الإلكتروني لتفعيله"}


@router.post("/verify-signup", response_model=TokenPair)
def verify_signup(payload: VerifySignupRequest, db: Session = Depends(get_db)):
    user_id = decode_email_verification_token(payload.token)

    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="رابط التحقق غير صالح أو منتهي الصلاحية")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="المستخدم غير موجود")

    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="الحساب مفعّل مسبقاً")

    user.is_verified = True
    db.commit()
    db.refresh(user)

    return _issue_token_pair(user, db)


@router.post("/login", response_model=TokenPair)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not user.password_hash or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="البريد الإلكتروني أو كلمة السر غير صحيحة")

    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="الرجاء تأكيد بريدك الإلكتروني أولاً")

    return _issue_token_pair(user, db)


@router.post("/refresh")
def refresh_access_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    stored_token = db.query(RefreshToken).filter(RefreshToken.token == payload.refresh_token).first()

    if not stored_token or stored_token.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="رمز التحديث غير صالح")

    if stored_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="رمز التحديث منتهي الصلاحية، يرجى تسجيل الدخول من جديد")

    user = db.query(User).filter(User.user_id == stored_token.user_id).first()
    new_access_token = create_access_token({"user_id": user.user_id, "role": user.role.value})

    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    stored_token = db.query(RefreshToken).filter(RefreshToken.token == payload.refresh_token).first()
    if stored_token:
        stored_token.revoked = True
        db.commit()
    return


@router.post("/google/signup", response_model=TokenPair)
def google_signup(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        idinfo = google_id_token.verify_oauth2_token(
            payload.id_token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="توكن Google غير صالح")

    email = idinfo["email"]
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="هذا البريد الإلكتروني مسجل مسبقاً. الرجاء تسجيل الدخول بدلاً من ذلك"
        )

    first_name = idinfo.get("given_name", "")
    last_name = idinfo.get("family_name", "")

    new_user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=None,
        role=UserRole.FARMER,
    )
    db.add(new_user)
    db.flush()

    farmer = Farmer(user_id=new_user.user_id, auth_provider="google")
    db.add(farmer)
    db.commit()
    db.refresh(new_user)

    return _issue_token_pair(new_user, db)


@router.post("/google/login", response_model=TokenPair)
def google_login(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        idinfo = google_id_token.verify_oauth2_token(
            payload.id_token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="توكن Google غير صالح")

    email = idinfo["email"]
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا يوجد حساب مرتبط بهذا البريد الإلكتروني. الرجاء إنشاء حساب أولاً"
        )

    return _issue_token_pair(user, db)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        token = create_password_reset_token(user.user_id)
        send_password_reset_link(user.email, token)

    return {"message": "إذا كان البريد الإلكتروني مسجلاً، ستصلك رسالة استرداد كلمة السر"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user_id = decode_password_reset_token(payload.token)

    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="رابط الاسترداد غير صالح أو منتهي الصلاحية")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="المستخدم غير موجود")

    user.password_hash = hash_password(payload.new_password)
    db.commit()

    return {"message": "تم تغيير كلمة السر بنجاح"}