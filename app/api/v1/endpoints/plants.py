from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.farmer import Farmer
from app.models.plant import Plant
from app.models.diagnosis import Diagnosis
from app.models.diseases import Diseases
from app.schemas.plant import PlantOut, PlantWithDiagnosesOut, DiagnosisSummary, DiagnosisHistoryOut

router = APIRouter(prefix="/plants", tags=["Plants"])


@router.get("", response_model=list[PlantOut])
def get_my_plants(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.user_id == current_user.user_id).first()
    if not farmer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذه الميزة متاحة للفلاحين فقط")

    return db.query(Plant).filter(Plant.farmer_id == farmer.farmer_id).order_by(Plant.created_at.desc()).all()


@router.get("/history", response_model=DiagnosisHistoryOut)
def get_diagnoses_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.user_id == current_user.user_id).first()
    if not farmer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذه الميزة متاحة للفلاحين فقط")

    plants = db.query(Plant).filter(Plant.farmer_id == farmer.farmer_id).order_by(Plant.created_at.desc()).all()

    plants_result = []
    for plant in plants:
        diagnoses = (
            db.query(Diagnosis, Diseases)
            .join(Diseases, Diagnosis.disease_id == Diseases.disease_id)
            .filter(Diagnosis.plant_id == plant.plant_id)
            .order_by(Diagnosis.diagnosed_at.desc())
            .all()
        )
        if not diagnoses:
            continue

        diagnosis_list = [
            DiagnosisSummary(
               diagnosis_id=d.diagnosis_id,
               disease_name=disease.name,
               description=disease.description,
               symptoms=disease.symptoms,
               treatment_plan=disease.treatment_plan,
               recommendations=disease.recommendations,
               confidence_score=d.confidence_score,
               image_url=d.image_url,
               diagnosed_at=d.diagnosed_at,
                )
            for d, disease in diagnoses
        ]
        plants_result.append(PlantWithDiagnosesOut(plant_id=plant.plant_id, nickname=plant.nickname, diagnoses=diagnosis_list))

    unlinked = (
        db.query(Diagnosis, Diseases)
        .join(Diseases, Diagnosis.disease_id == Diseases.disease_id)
        .filter(Diagnosis.farmer_id == farmer.farmer_id, Diagnosis.plant_id.is_(None))
        .order_by(Diagnosis.diagnosed_at.desc())
        .all()
    )
    unlinked_result = [
        DiagnosisSummary(
            diagnosis_id=d.diagnosis_id, disease_name=disease.name, symptoms=disease.symptoms,
            treatment_recommendations=disease.treatment_recommendations, confidence_score=d.confidence_score,
            image_url=d.image_url, diagnosed_at=d.diagnosed_at,
        )
        for d, disease in unlinked
    ]

    return DiagnosisHistoryOut(plants=plants_result, unlinked_diagnoses=unlinked_result)