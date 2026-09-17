from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.farmer import Farmer
from app.models.diagnosis import Diagnosis
from app.models.diseases import Diseases
from app.schemas.admin import (
    UserListItem, PaginatedUsers, UserSearchRequest,
    DiseaseCreate, DiseaseUpdate, AdminDiagnosisItem, StatisticsOut,
)
from app.schemas.disease import DiseaseOut

router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------- US-ADM-01: عرض قائمة المستخدمين ----------
@router.get("/users", response_model=PaginatedUsers)
def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total = db.query(User).count()
    users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedUsers(total=total, page=page, page_size=page_size, users=users)


# ---------- US-ADM-02: حذف مستخدم ----------
@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المستخدم غير موجود")

    db.delete(user)
    db.commit()
    return


# ---------- US-ADM-03: البحث عن مستخدم بالإيميل ----------
@router.get("/users/search", response_model=UserListItem)
def search_user_by_email(
    email: str = Query(...),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="لم يتم العثور على مستخدم بهذا البريد الإلكتروني")
    return user


# ---------- US-ADM-04: عرض قاموس الأمراض (للأدمن تحديداً، نفس /diseases العامة تقريباً) ----------
@router.get("/diseases", response_model=list[DiseaseOut])
def get_all_diseases_admin(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return db.query(Diseases).order_by(Diseases.name).all()


# ---------- US-ADM-05: إضافة مرض جديد ----------
@router.post("/diseases", response_model=DiseaseOut, status_code=status.HTTP_201_CREATED)
def create_disease(
    payload: DiseaseCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(Diseases).filter(Diseases.name_en == payload.name_en).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="هذا المرض موجود مسبقاً بقاموس الأمراض")

    new_disease = Diseases(**payload.model_dump())
    db.add(new_disease)
    db.commit()
    db.refresh(new_disease)
    return new_disease


# ---------- US-ADM-06: تعديل مرض موجود ----------
@router.put("/diseases/{disease_id}", response_model=DiseaseOut)
def update_disease(
    disease_id: int,
    payload: DiseaseUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    disease = db.query(Diseases).filter(Diseases.disease_id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="المرض غير موجود")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(disease, key, value)

    db.commit()
    db.refresh(disease)
    return disease


# ---------- US-ADM-07: عرض سجل تشخيصات مستخدم معيّن ----------
@router.get("/users/{user_id}/diagnoses", response_model=list[AdminDiagnosisItem])
def get_user_diagnoses(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    farmer = db.query(Farmer).filter(Farmer.user_id == user_id).first()
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="لا يوجد فلاح بهذا المعرف")

    diagnoses = (
        db.query(Diagnosis, Diseases)
        .join(Diseases, Diagnosis.disease_id == Diseases.disease_id)
        .filter(Diagnosis.farmer_id == farmer.farmer_id)
        .order_by(Diagnosis.diagnosed_at.desc())
        .all()
    )

    return [
        AdminDiagnosisItem(
            diagnosis_id=d.diagnosis_id,
            disease_name=disease.name,
            confidence_score=d.confidence_score,
            diagnosed_at=d.diagnosed_at,
        )
        for d, disease in diagnoses
    ]


# ---------- US-ADM-08: الإحصائيات العامة ----------
@router.get("/statistics", response_model=StatisticsOut)
def get_statistics(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total_diagnoses = db.query(Diagnosis).count()
    total_farmers = db.query(Farmer).count()

    most_common = (
        db.query(Diseases.name, func.count(Diagnosis.diagnosis_id).label("count"))
        .join(Diagnosis, Diagnosis.disease_id == Diseases.disease_id)
        .group_by(Diseases.name)
        .order_by(func.count(Diagnosis.diagnosis_id).desc())
        .limit(5)
        .all()
    )

    return StatisticsOut(
        total_diagnoses=total_diagnoses,
        total_farmers=total_farmers,
        most_common_diseases=[{"disease_name": name, "count": count} for name, count in most_common],
    )