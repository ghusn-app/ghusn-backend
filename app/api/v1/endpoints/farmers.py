from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.farmer import Farmer
from app.models.diagnosis import Diagnosis
from app.models.plant import Plant
from app.schemas.farmer import FarmerProfileOut

router = APIRouter(prefix="/farmers", tags=["Farmers"])


@router.get("/me", response_model=FarmerProfileOut)
def get_my_farmer_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = db.query(Farmer).filter(Farmer.user_id == current_user.user_id).first()
    if not farmer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذه الميزة متاحة للفلاحين فقط")

    total_diagnoses = db.query(Diagnosis).filter(Diagnosis.farmer_id == farmer.farmer_id).count()
    total_plants = db.query(Plant).filter(Plant.farmer_id == farmer.farmer_id).count()

    return FarmerProfileOut(
        user_id=current_user.user_id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        role=current_user.role.value,
        created_at=current_user.created_at,
        auth_provider=farmer.auth_provider.value,
        total_diagnoses=total_diagnoses,
        total_plants=total_plants,
    )