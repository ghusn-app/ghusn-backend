from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Plant(Base):
    __tablename__ = "plants"

    plant_id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.farmer_id", ondelete="CASCADE"), nullable=False)
    nickname = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    farmer = relationship("Farmer", back_populates="plants")
    diagnoses = relationship("Diagnosis", back_populates="plant")