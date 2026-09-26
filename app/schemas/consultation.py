from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.models.consultation import ConsultationStatus


# =========================================================
# CREATE CONSULTATION
# Farmer creates a consultation request
# =========================================================

class ConsultationCreate(BaseModel):
    expert_id: int
    ai_diagnosis_id: int | None = None


# =========================================================
# CONSULTATION RESPONSE
# =========================================================

class ConsultationOut(BaseModel):
    consultation_id: int

    farmer_id: int
    expert_id: int

    ai_diagnosis_id: int | None = None
    expert_diagnosis_id: int | None = None

    status: ConsultationStatus

    questions_used: int
    max_questions: int

    created_at: datetime
    accepted_at: datetime | None = None
    closed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)