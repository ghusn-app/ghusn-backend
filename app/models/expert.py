import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime,Boolean,Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Expert(Base):
    __tablename__ = "experts"

    expert_id = Column(Integer, primary_key=True, index=True)
    user_id = Column( Integer, ForeignKey("users.user_id"), unique=True, nullable=False)
    specialization = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    experience_years = Column( Integer, nullable=False, default=0)
    consultation_price = Column( Numeric(10, 2), nullable=False)
    is_available = Column( Boolean, default=True, nullable=False)
    created_at = Column( DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="expert" )

    consultations = relationship("Consultation",back_populates="expert")