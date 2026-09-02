from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from datetime import datetime

class UserSignup(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    confirm_password: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        has_letter = any(c.isalpha() for c in value)
        has_digit = any(c.isdigit() for c in value)
        has_symbol = any(not c.isalnum() for c in value)

        if not (has_letter and has_digit and has_symbol):
            raise ValueError("كلمة السر لازم تحتوي على حرف ورقم ورمز واحد على الأقل")
        return value

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("كلمة السر وتأكيد كلمة السر غير متطابقين")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    refresh_token_expires_at: datetime
class RefreshRequest(BaseModel):
    refresh_token: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    email: EmailStr
    code: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)
    confirm_new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        has_letter = any(c.isalpha() for c in value)
        has_digit = any(c.isdigit() for c in value)
        has_symbol = any(not c.isalnum() for c in value)
        if not (has_letter and has_digit and has_symbol):
            raise ValueError("كلمة السر لازم تحتوي على حرف ورقم ورمز واحد على الأقل")
        return value

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError("كلمة السر الجديدة وتأكيدها غير متطابقين")
        return self

class VerifySignupRequest(BaseModel):
    token: str