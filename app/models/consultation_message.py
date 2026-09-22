
from sqlalchemy import Column, Integer, String, DateTime,ForeignKey,Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ConsultationMessage(Base):
    __tablename__ = "consultation_messages"

    message_id = Column( Integer,primary_key=True,index=True)
    consultation_id = Column(Integer,ForeignKey("consultations.consultation_id"),nullable=False)
    sender_id = Column(Integer,ForeignKey("users.user_id"),nullable=False)
    message = Column(Text,nullable=True)
    image_url = Column( String, nullable=True)
    created_at = Column( DateTime(timezone=True), server_default=func.now())

    # Relationships
    consultation = relationship("Consultation",back_populates="messages")
    sender = relationship("User",back_populates="sent_consultation_messages")