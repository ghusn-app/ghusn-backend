import enum
from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

# 1. تعريف فئة Enum لمزودي خدمة التوثيق
class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"

class Farmer(Base):
    __tablename__ = "farmers"

    farmer_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # 2. تعيين نوع الحقل كـ Enum
    auth_provider = Column(
        Enum(AuthProvider, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=AuthProvider.LOCAL
    )

    # العلاقات
    user = relationship("User", back_populates="farmer_profile")
    diagnoses = relationship("Diagnosis", back_populates="farmer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="farmer", cascade="all, delete-orphan")
    plants = relationship("Plant", back_populates="farmer", cascade="all, delete-orphan")
    consultations = relationship("Consultation",back_populates="farmer")
    payments = relationship("Payment",back_populates="farmer")