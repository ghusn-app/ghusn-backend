from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.admin import Admin
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="التوكن غير صالح أو منتهي الصلاحية",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="المستخدم غير موجود")

    return user


def get_current_admin(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    admin = db.query(Admin).filter(Admin.user_id == current_user.user_id).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذه الميزة متاحة للمسؤولين فقط")
    return current_user