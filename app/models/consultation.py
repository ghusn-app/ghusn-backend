import enum
from sqlalchemy import Column, Integer, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ConsultationStatus(str, enum.Enum):
     PENDING_EXPERT = "pending_expert"
     PENDING_PAYMENT = "pending_payment"
     OPEN = "open"
     WAITING_EXPERT = "waiting_expert"
     WAITING_FARMER = "waiting_farmer"
     REJECTED = "rejected"
     CLOSED = "closed"
class Consultation(Base):
    __tablename__ = "consultations"

    consultation_id = Column( Integer, primary_key=True, index=True)
    farmer_id = Column(Integer,ForeignKey("farmers.farmer_id"),nullable=False)
    expert_id = Column(Integer,ForeignKey("experts.expert_id"),nullable=False)
    ai_diagnosis_id = Column(Integer,ForeignKey("diagnoses.diagnosis_id"),nullable=True)
    expert_diagnosis_id = Column(Integer,ForeignKey("diagnoses.diagnosis_id"),nullable=True)
    status = Column(Enum(ConsultationStatus),nullable=False,default=ConsultationStatus.PENDING_PAYMENT)
    questions_used = Column(Integer,nullable=False,default=0)
    max_questions = Column( Integer, nullable=False, default=3)
    created_at = Column( DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True),nullable=True)

    # Relationships
    farmer = relationship("Farmer",back_populates="consultations")
    expert = relationship( "Expert", back_populates="consultations")
    diagnosis = relationship("Diagnosis", back_populates="consultations")
    messages = relationship("ConsultationMessage",back_populates="consultation")
    payments = relationship( "Payment", back_populates="consultation")
    notifications = relationship("Notification",back_populates="consultation" )