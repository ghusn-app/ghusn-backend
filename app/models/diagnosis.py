import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime,Text,Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class DiagnosisSource(str, enum.Enum):
    AI = "ai"
    EXPERT = "expert"


class DiagnosisStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    UNCERTAIN = "uncertain"

class Diagnosis(Base):
    __tablename__ = "diagnoses"

    diagnosis_id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.farmer_id", ondelete="CASCADE"), nullable=False)
    plant_id = Column(Integer, ForeignKey("plants.plant_id", ondelete="SET NULL"), nullable=True)
    disease_id = Column(Integer, ForeignKey("diseases.disease_id"), nullable=True)
    disease_name_by_expert = Column(String,nullable=True)
    image_url = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    source = Column(Enum(DiagnosisSource),nullable=False)
    status = Column(Enum(DiagnosisStatus),nullable=False)
    diagnosed_at = Column(DateTime(timezone=True), server_default=func.now())

    # العلاقات
    farmer = relationship("Farmer", back_populates="diagnoses")
    disease = relationship("Diseases", back_populates="diagnoses")
    payment = relationship("Payment", back_populates="diagnosis", uselist=False)
    plant = relationship("Plant", back_populates="diagnoses")