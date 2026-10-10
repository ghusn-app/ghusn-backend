from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConsultationMessageCreate(BaseModel):
    message: str


class ConsultationMessageOut(BaseModel):
    message_id: int
    consultation_id: int
    sender_id: int
    message: str | None
    image_url: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)