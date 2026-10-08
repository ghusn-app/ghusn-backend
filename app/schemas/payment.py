from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.payments import PaymentStatus


# =========================================================
# CREATE PAYMENT
# =========================================================

class PaymentCreate(BaseModel):
    consultation_id: int


# =========================================================
# PAYMENT RESPONSE
# =========================================================

class PaymentOut(BaseModel):
    payment_id: int
    consultation_id: int
    farmer_id: int

    amount: Decimal
    currency: str

    status: PaymentStatus

    payment_method: str | None = None
    transaction_id: str | None = None

    created_at: datetime
    paid_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)