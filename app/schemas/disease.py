from pydantic import BaseModel


class DiseaseOut(BaseModel):
    disease_id: int
    name: str
    description: str | None
    symptoms: str | None
    treatment_plan: str | None
    recommendations: str | None

    class Config:
        from_attributes = True