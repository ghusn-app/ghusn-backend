import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime,Boolean,Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class NotificationType(str, enum.Enum):
    NEW_CONSULTATION = "new_consultation"

    CONSULTATION_ACCEPTED = "consultation_accepted"
    CONSULTATION_REJECTED = "consultation_rejected"

    PAYMENT_SUCCESS = "payment_success"

    NEW_FARMER_MESSAGE = "new_farmer_message"
    EXPERT_REPLY = "expert_reply"

    CONSULTATION_CLOSED = "consultation_closed"


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer,primary_key=True,index=True)
    user_id = Column(Integer,ForeignKey("users.user_id"),nullable=False)
    consultation_id = Column(Integer,ForeignKey("consultations.consultation_id"),nullable=True)
    type = Column(Enum(NotificationType),nullable=False)
    title = Column(String,nullable=False)
    message = Column( Text, nullable=False)
    is_read = Column(Boolean,default=False,nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now())

    # Relationships
    user = relationship("User",back_populates="notifications")
    consultation = relationship("Consultation",back_populates="notifications")