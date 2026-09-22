from pydantic import BaseModel
from datetime import datetime

from app.models.diagnosis import Diagnosis,DiagnosisSource, DiagnosisStatus


class DiagnosisOut(BaseModel):
    diagnosis_id: int

    # قد يكون NULL في تشخيص الخبير إذا كتب مرضًا
    # غير موجود في diseases table
    disease_id: int | None = None

    disease_name: str | None = None

    # يستخدم عندما يشخص الخبير مرضًا
    # غير موجود في diseases table
    disease_name_by_expert: str | None = None

    description: str | None = None

    # AI diagnosis → يوجد confidence
    # Expert diagnosis → NULL
    confidence_score: float | None = None

    # Expert diagnosis قد لا يحتوي صورة خاصة به
    image_url: str | None = None

    diagnosed_at: datetime

    symptoms: str | None = None
    treatment_plan: str | None = None
    recommendations: str | None = None

    # AI أو EXPERT
    source: DiagnosisSource

    # PENDING / CONFIRMED / UNCERTAIN
    status: DiagnosisStatus

    # ربط التشخيص بالشجرة
    plant_id: int | None = None
    plant_nickname: str | None = None

    class Config:
        from_attributes = True