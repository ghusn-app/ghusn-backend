from pydantic import BaseModel, Field, model_validator
from datetime import datetime


class DiagnosisSummary(BaseModel):
    diagnosis_id: int
    disease_name: str
    description: str | None
    symptoms: str | None
    treatment_plan: str | None
    recommendations: str | None
    confidence_score: float
    image_url: str
    diagnosed_at: datetime

    class Config:
        from_attributes = True


class LinkPlantRequest(BaseModel):
    plant_id: int | None = None
    nickname: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_one_option(self):
        if not self.plant_id and not self.nickname:
            raise ValueError("يجب تحديد نبتة موجودة (plant_id) أو اسم نبتة جديدة (nickname)")
        if self.plant_id and self.nickname:
            raise ValueError("حددي إما نبتة موجودة أو نبتة جديدة، وليس كلاهما")
        return self


class DiagnosisSummary(BaseModel):
    diagnosis_id: int
    disease_name: str
    symptoms: str | None
    treatment_recommendations: str | None
    confidence_score: float
    image_url: str
    diagnosed_at: datetime

    class Config:
        from_attributes = True


class PlantWithDiagnosesOut(BaseModel):
    plant_id: int
    nickname: str
    diagnoses: list[DiagnosisSummary]

    class Config:
        from_attributes = True


class DiagnosisHistoryOut(BaseModel):
    plants: list[PlantWithDiagnosesOut]
    unlinked_diagnoses: list[DiagnosisSummary]