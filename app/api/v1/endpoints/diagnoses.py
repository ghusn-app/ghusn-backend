from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.farmer import Farmer
from app.models.diagnosis import Diagnosis
from app.models.diseases import Diseases
from app.schemas.diagnosis import DiagnosisOut
from app.services.storage_service import save_diagnosis_image
from app.services.ai_integration import analyze_plant_image

from app.models.plant import Plant
from app.schemas.plant import LinkPlantRequest

router = APIRouter(prefix="/diagnoses", tags=["Diagnoses"])
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


@router.post("", response_model=DiagnosisOut, status_code=status.HTTP_201_CREATED)
def create_diagnosis(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = db.query(Farmer).filter(Farmer.user_id == current_user.user_id).first()
    if not farmer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذه الميزة متاحة للفلاحين فقط")

    if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="صيغة الصورة غير مدعومة. الصيغ المسموحة: JPG, JPEG, PNG")

    image_bytes = image.file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"حجم الصورة كبير جداً. الحد الأقصى المسموح {MAX_IMAGE_SIZE_MB} ميجابايت")
    image.file.seek(0)

    image_url = save_diagnosis_image(image)
    ai_result = analyze_plant_image(image_url)

    if not ai_result["is_confident"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="لم يتمكن النظام من تحديد المرض بثقة كافية. الرجاء إعادة المحاولة بصورة أوضح"
        )

    disease = db.query(Diseases).filter(Diseases.name == ai_result["disease_name"]).first()
    if not disease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المرض المكتشف غير موجود بقاعدة البيانات")

    new_diagnosis = Diagnosis(
        farmer_id=farmer.farmer_id,
        disease_id=disease.disease_id,
        image_url=image_url,
        confidence_score=ai_result["confidence_score"],
    )
    db.add(new_diagnosis)
    db.commit()
    db.refresh(new_diagnosis)

    return DiagnosisOut(
        diagnosis_id=new_diagnosis.diagnosis_id,
        disease_id=disease.disease_id,
        disease_name=disease.name,
        confidence_score=new_diagnosis.confidence_score,
        image_url=new_diagnosis.image_url,
        diagnosed_at=new_diagnosis.diagnosed_at,
        treatment_recommendations=disease.treatment_recommendations,
    )


@router.get("/my", response_model=list[DiagnosisOut])
def get_my_diagnoses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = db.query(Farmer).filter(Farmer.user_id == current_user.user_id).first()
    if not farmer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذه الميزة متاحة للفلاحين فقط")

    diagnoses = (
        db.query(Diagnosis, Diseases)
        .join(Diseases, Diagnosis.disease_id == Diseases.disease_id)
        .filter(Diagnosis.farmer_id == farmer.farmer_id)
        .order_by(Diagnosis.diagnosed_at.desc())
        .all()
    )

    return [
        DiagnosisOut(
            diagnosis_id=d.diagnosis_id,
            disease_id=disease.disease_id,
            disease_name=disease.name,
            confidence_score=d.confidence_score,
            image_url=d.image_url,
            diagnosed_at=d.diagnosed_at,
            treatment_recommendations=disease.treatment_recommendations,
        )
        for d, disease in diagnoses
    ]


@router.get("/{diagnosis_id}", response_model=DiagnosisOut)
def get_diagnosis_by_id(
    diagnosis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = db.query(Farmer).filter(Farmer.user_id == current_user.user_id).first()
    if not farmer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذه الميزة متاحة للفلاحين فقط")

    result = (
        db.query(Diagnosis, Diseases)
        .join(Diseases, Diagnosis.disease_id == Diseases.disease_id)
        .filter(Diagnosis.diagnosis_id == diagnosis_id, Diagnosis.farmer_id == farmer.farmer_id)
        .first()
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="التشخيص غير موجود")

    diagnosis, disease = result
    return DiagnosisOut(
        diagnosis_id=diagnosis.diagnosis_id,
        disease_id=disease.disease_id,
        disease_name=disease.name,
        confidence_score=diagnosis.confidence_score,
        image_url=diagnosis.image_url,
        diagnosed_at=diagnosis.diagnosed_at,
        treatment_recommendations=disease.treatment_recommendations,
    )

@router.patch("/{diagnosis_id}/plant", response_model=DiagnosisOut)
def link_diagnosis_to_plant(
    diagnosis_id: int, payload: LinkPlantRequest,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    farmer = db.query(Farmer).filter(Farmer.user_id == current_user.user_id).first()
    if not farmer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="هذه الميزة متاحة للفلاحين فقط")

    diagnosis = db.query(Diagnosis).filter(
        Diagnosis.diagnosis_id == diagnosis_id, Diagnosis.farmer_id == farmer.farmer_id
    ).first()
    if not diagnosis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="التشخيص غير موجود")

    if payload.plant_id:
        plant = db.query(Plant).filter(
            Plant.plant_id == payload.plant_id, Plant.farmer_id == farmer.farmer_id
        ).first()
        if not plant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="النبتة غير موجودة")
    else:
        plant = Plant(farmer_id=farmer.farmer_id, nickname=payload.nickname)
        db.add(plant)
        db.flush()

    diagnosis.plant_id = plant.plant_id
    db.commit()
    db.refresh(diagnosis)

    disease = db.query(Diseases).filter(Diseases.disease_id == diagnosis.disease_id).first()
    return DiagnosisOut(
        diagnosis_id=diagnosis.diagnosis_id, disease_id=disease.disease_id, disease_name=disease.name,
        confidence_score=diagnosis.confidence_score, image_url=diagnosis.image_url,
        diagnosed_at=diagnosis.diagnosed_at, treatment_recommendations=disease.treatment_recommendations,
    )