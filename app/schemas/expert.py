from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ==========================================
# EXPERT BASE
# ==========================================

class ExpertBase(BaseModel):
    specialization: str
    bio: str | None = None
    experience_years: int
    consultation_price: Decimal


# ==========================================
# CREATE EXPERT
# ==========================================

class ExpertCreate(ExpertBase):
    user_id: int


# ==========================================
# ADMIN CREATE EXPERT ACCOUNT
# ==========================================

class AdminExpertCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str = Field(min_length=8)

    specialization: str
    bio: str | None = None
    experience_years: int = Field(ge=0)
    consultation_price: Decimal = Field(gt=0)


# ==========================================
# UPDATE EXPERT
# ==========================================

class ExpertUpdate(BaseModel):
    specialization: str | None = None
    bio: str | None = None
    experience_years: int | None = None
    consultation_price: Decimal | None = None
    is_available: bool | None = None


# ==========================================
# UPDATE AVAILABILITY
# ==========================================

class ExpertAvailabilityUpdate(BaseModel):
    is_available: bool


# ==========================================
# EXPERT RESPONSE
# ==========================================

class ExpertOut(BaseModel):
    expert_id: int
    user_id: int

    specialization: str
    bio: str | None = None
    experience_years: int
    consultation_price: Decimal
    is_available: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)