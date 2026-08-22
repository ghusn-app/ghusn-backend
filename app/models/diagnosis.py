from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime,Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Diagnosis(Base):
    __tablename__ = "diagnoses"

    diagnosis_id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.farmer_id", ondelete="CASCADE"), nullable=False)
    disease_id = Column(Integer, ForeignKey("diseases.disease_id"), nullable=False)
    image_url = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    diagnosed_at = Column(DateTime(timezone=True), server_default=func.now())

    # العلاقات
    farmer = relationship("Farmer", back_populates="diagnoses")
    disease = relationship("Diseases", back_populates="diagnoses")
    payment = relationship("Payment", back_populates="diagnosis", uselist=False)