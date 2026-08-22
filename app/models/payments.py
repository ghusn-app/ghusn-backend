
import enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
# payment.py — diagnosis_id يرجع FK إلزامي هون
class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.farmer_id", ondelete="CASCADE"), nullable=False)
    diagnosis_id = Column(Integer, ForeignKey("diagnoses.diagnosis_id"), nullable=False, unique=True)
    admin_id = Column(Integer, ForeignKey("admins.admin_id"), nullable=True)

    currency = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    provider = Column(String(50), nullable=False)
    payment_status = Column(
        Enum(PaymentStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=PaymentStatus.PENDING
    )
    transaction_ref = Column(String(100), nullable=True)

    farmer = relationship("Farmer", back_populates="payments")
    admin = relationship("Admin", back_populates="approved_payments")
    diagnosis = relationship("Diagnosis", back_populates="payment")