from pydantic import BaseModel
from datetime import datetime


class DiagnosisOut(BaseModel):
    diagnosis_id: int
    disease_id: int
    disease_name: str
    description: str | None = None
    confidence_score: float
    image_url: str
    diagnosed_at: datetime
    symptoms: str | None = None
    treatment_plan: str | None = None
    recommendations: str | None = None

    class Config:
        from_attributes = True