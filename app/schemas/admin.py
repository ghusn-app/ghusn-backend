from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserListItem(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedUsers(BaseModel):
    total: int
    page: int
    page_size: int
    users: list[UserListItem]


class UserSearchRequest(BaseModel):
    email: EmailStr


class DiseaseCreate(BaseModel):
    name_en: str
    name: str
    description: str
    symptoms: str
    treatment_plan: str
    recommendations: str


class DiseaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    symptoms: str | None = None
    treatment_plan: str | None = None
    recommendations: str | None = None


class AdminDiagnosisItem(BaseModel):
    diagnosis_id: int
    disease_name: str
    confidence_score: float
    diagnosed_at: datetime

    class Config:
        from_attributes = True


class StatisticsOut(BaseModel):
    total_diagnoses: int
    total_farmers: int
    most_common_diseases: list[dict]