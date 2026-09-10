from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Diseases(Base):
    __tablename__ = "diseases"

    disease_id = Column(Integer, primary_key=True, index=True)
    name_en = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=False)
    symptoms = Column(Text, nullable=False)
    treatment_plan = Column(Text, nullable=False)
    recommendations = Column(Text, nullable=False)
    

    # العلاقات
    diagnoses = relationship("Diagnosis", back_populates="disease")