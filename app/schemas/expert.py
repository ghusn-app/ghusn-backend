from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal


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
# Used by Admin later
# ==========================================

class ExpertCreate(ExpertBase):
    user_id: int


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

class ExpertAvailabilityUpdate(BaseModel):
    is_available: bool

    model_config = ConfigDict(from_attributes=True)