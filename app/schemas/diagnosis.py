from pydantic import BaseModel
from datetime import datetime


class DiagnosisOut(BaseModel):
    diagnosis_id: int
    disease_id: int
    disease_name: str
    confidence_score: float
    image_url: str
    diagnosed_at: datetime
    treatment_recommendations: str | None = None

    class Config:
        from_attributes = True