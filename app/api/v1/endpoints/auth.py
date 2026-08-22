from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.models.farmer import Farmer
from app.models.refresh_token import RefreshToken
from app.schemas.user import UserSignup, UserLogin, TokenPair, RefreshRequest,GoogleAuthRequest
from app.security import hash_password, verify_password, create_access_token, create_refresh_token

import os
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

import random
from app.models.password_reset import PasswordReset
from app.schemas.user import ForgotPasswordRequest, VerifyResetCodeRequest, ResetPasswordRequest
from app.services.email_service import send_password_reset_code

RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES"))


router = APIRouter(prefix="/auth", tags=["Auth"])
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


def _issue_token_pair(user: User, db: Session) -> TokenPair:
    """دالة مساعدة: بتولّد access + refresh token مع بعض، وبتخزّن الـrefresh بقاعدة البيانات
    (تستخدم بس وقت signup/login، مش وقت refresh)"""
    access_token = create_access_token({"user_id": user.user_id, "role": user.role.value})

    refresh_token_value, refresh_expires_at = create_refresh_token()
    new_refresh = RefreshToken(
        token=refresh_token_value,
        user_id=user.user_id,
        expires_at=refresh_expires_at,
    )
    db.add(new_refresh)
    db.commit()

    return TokenPair(access_token=access_token, refresh_token=refresh_token_value)


@router.post("/signup", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
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
    )
    db.add(new_user)
    db.flush()

    new_farmer = Farmer(user_id=new_user.user_id)
    db.add(new_farmer)
    db.commit()
    db.refresh(new_user)

    return _issue_token_pair(new_user, db)


@router.post("/login", response_model=TokenPair)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not user.password_hash or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="البريد الإلكتروني أو كلمة السر غير صحيحة")

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


@router.post("/google", response_model=TokenPair)
def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        idinfo = google_id_token.verify_oauth2_token(
            payload.id_token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="توكن Google غير صالح")

    email = idinfo["email"]
    first_name = idinfo.get("given_name", "")
    last_name = idinfo.get("family_name", "")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=None,
            role=UserRole.FARMER,
        )
        db.add(user)
        db.flush()

        farmer = Farmer(user_id=user.user_id, auth_provider="google")
        db.add(farmer)
        db.commit()
        db.refresh(user)

    return _issue_token_pair(user, db)



@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if user:
        code = f"{random.randint(0, 999999):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)

        new_reset = PasswordReset(code=code, user_id=user.user_id, expires_at=expires_at)
        db.add(new_reset)
        db.commit()

        send_password_reset_code(user.email, code)

    return {"message": "إذا كان البريد الإلكتروني مسجلاً، ستصلك رسالة فيها رمز التحقق"}


@router.post("/verify-reset-code", status_code=status.HTTP_200_OK)
def verify_reset_code(payload: VerifyResetCodeRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="رمز التحقق غير صحيح")

    reset_entry = (
        db.query(PasswordReset)
        .filter(PasswordReset.user_id == user.user_id, PasswordReset.code == payload.code, PasswordReset.used == False)
        .order_by(PasswordReset.created_at.desc())
        .first()
    )

    if not reset_entry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="رمز التحقق غير صحيح")

    if reset_entry.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="رمز التحقق منتهي الصلاحية")

    return {"message": "رمز التحقق صحيح"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="رمز التحقق غير صحيح")

    reset_entry = (
        db.query(PasswordReset)
        .filter(PasswordReset.user_id == user.user_id, PasswordReset.code == payload.code, PasswordReset.used == False)
        .order_by(PasswordReset.created_at.desc())
        .first()
    )

    if not reset_entry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="رمز التحقق غير صحيح")

    if reset_entry.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="رمز التحقق منتهي الصلاحية")

    user.password_hash = hash_password(payload.new_password)
    reset_entry.used = True
    db.commit()

    return {"message": "تم تغيير كلمة السر بنجاح"}