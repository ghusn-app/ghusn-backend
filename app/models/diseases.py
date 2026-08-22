from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Diseases(Base):
    __tablename__ = "diseases"

    disease_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    symptoms = Column(Text, nullable=True)
    treatment_recommendations = Column(Text, nullable=True)
    

    # العلاقات
    diagnoses = relationship("Diagnosis", back_populates="disease")