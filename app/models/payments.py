
import enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
# payment.py — diagnosis_id يرجع FK إلزامي هون
class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(Integer,primary_key=True,index=True)
    consultation_id = Column(Integer,ForeignKey("consultations.consultation_id"),nullable=False)
    farmer_id = Column(Integer,ForeignKey("farmers.farmer_id"),nullable=False)
    amount = Column(Numeric(10, 2),nullable=False)
    currency = Column(String(10),nullable=False,default="ILS")
    status = Column(Enum(PaymentStatus),nullable=False,default=PaymentStatus.PENDING)
    payment_method = Column(String,nullable=True)
    transaction_id = Column(String,unique=True,nullable=True)
    created_at = Column(DateTime(timezone=True),server_default=func.now())
    paid_at = Column(DateTime(timezone=True),nullable=True)

    # Relationships
    consultation = relationship("Consultation",back_populates="payments")
    farmer = relationship("Farmer",back_populates="payments")