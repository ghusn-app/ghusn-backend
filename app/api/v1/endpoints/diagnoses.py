from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.farmer import Farmer
from app.models.diagnosis import Diagnosis
from app.models.diseases import Diseases
from app.models.plant import Plant
from app.schemas.diagnosis import DiagnosisOut
from app.schemas.plant import LinkPlantRequest
from app.services.storage_service import save_diagnosis_image
from app.services.ai_integration import analyze_plant_image
import os
import tempfile

router = APIRouter(prefix="/diagnoses", tags=["Diagnoses"])
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

allowed_content_types = ["image/jpeg", "image/png"]
allowed_extensions = ["jpg", "jpeg", "png"]



@router.post("", response_model=DiagnosisOut, status_code=status.HTTP_201_CREATED)
def create_diagnosis(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = (
        db.query(Farmer)
        .filter(Farmer.user_id == current_user.user_id)
        .first()
    )

    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذه الميزة متاحة للفلاحين فقط"
        )

    # 1. Validate type and extension
    file_extension = image.filename.rsplit(".", 1)[-1].lower()

    if (
        image.content_type not in allowed_content_types
        or file_extension not in allowed_extensions
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="صيغة الصورة غير مدعومة. الصيغ المسموحة: JPG, JPEG, PNG"
        )

    # 2. Read bytes
    image_bytes = image.file.read()

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="الصورة فارغة"
        )

    if len(image_bytes) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"حجم الصورة كبير جداً. الحد الأقصى المسموح {MAX_IMAGE_SIZE_MB} ميجابايت"
        )

    temp_path = None

    try:
        # 3. Temporary file for AI only
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{file_extension}"
        ) as temp_file:
            temp_file.write(image_bytes)
            temp_path = temp_file.name

        # 4. AI diagnosis first
        ai_result = analyze_plant_image(temp_path)

        if not ai_result["is_confident"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="لم يتمكن النظام من تحديد المرض بثقة كافية. الرجاء إعادة المحاولة بصورة أوضح"
            )

        # 5. Check disease exists in DB
       
        disease = (
            db.query(Diseases)
            .filter(
                Diseases.name_en == ai_result["disease_name"]
            )
            .first()
        )
       

        if not disease:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="المرض المكتشف غير موجود بقاعدة البيانات"
            )

        # 6. Save image only AFTER successful diagnosis
        image_url = save_diagnosis_image(
            image_bytes=image_bytes,
            original_filename=image.filename,
            content_type=image.content_type,
            farmer_id=farmer.farmer_id
        )

        # 7. Save diagnosis in PostgreSQL
        new_diagnosis = Diagnosis(
            farmer_id=farmer.farmer_id,
            disease_id=disease.disease_id,
            image_url=image_url,
            confidence_score=ai_result["confidence_score"],
            plant_id=None,
        )

        db.add(new_diagnosis)
        db.commit()
        db.refresh(new_diagnosis)

        return DiagnosisOut(
            diagnosis_id=new_diagnosis.diagnosis_id,
            disease_id=disease.disease_id,
            disease_name=disease.name,
            description=disease.description,
            confidence_score=new_diagnosis.confidence_score,
            image_url=new_diagnosis.image_url,
            diagnosed_at=new_diagnosis.diagnosed_at,
            symptoms=disease.symptoms,
            treatment_plan=disease.treatment_plan,
            recommendations=disease.recommendations,
            plant_id=None,
            plant_nickname=None,
        )

    finally:
        # 8. Always delete temp file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


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
            description=disease.description,
            confidence_score=d.confidence_score,
            image_url=d.image_url,
            diagnosed_at=d.diagnosed_at,
            symptoms=disease.symptoms,
            treatment_plan=disease.treatment_plan,
            recommendations=disease.recommendations,
            plant_id=d.plant_id,
            plant_nickname=d.plant.nickname if d.plant else None,
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
        description=disease.description,
        confidence_score=diagnosis.confidence_score,
        image_url=diagnosis.image_url,
        diagnosed_at=diagnosis.diagnosed_at,
        symptoms=disease.symptoms,
        treatment_plan=disease.treatment_plan,
        recommendations=disease.recommendations,
        plant_id=diagnosis.plant_id,
        plant_nickname=diagnosis.plant.nickname if diagnosis.plant else None,
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
        diagnosis_id=diagnosis.diagnosis_id,
        disease_id=disease.disease_id,
        disease_name=disease.name,
        description=disease.description,
        confidence_score=diagnosis.confidence_score,
        image_url=diagnosis.image_url,
        diagnosed_at=diagnosis.diagnosed_at,
        symptoms=disease.symptoms,
        treatment_plan=disease.treatment_plan,
        recommendations=disease.recommendations,
        plant_id=diagnosis.plant_id,
        plant_nickname=plant.nickname,
    )