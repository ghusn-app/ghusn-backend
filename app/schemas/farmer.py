from pydantic import BaseModel, EmailStr
from datetime import datetime


class FarmerProfileOut(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: str
    created_at: datetime
    auth_provider: str
    total_diagnoses: int
    total_plants: int

    class Config:
        from_attributes = True