from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user

from app.models.user import User
from app.models.farmer import Farmer
from app.models.expert import Expert
from app.models.diagnosis import Diagnosis, DiagnosisSource
from app.models.consultation import Consultation, ConsultationStatus

from app.schemas.consultation import (
    ConsultationCreate,
    ConsultationOut,
)


router = APIRouter(
    prefix="/consultations",
    tags=["Consultations"]
)


# =========================================================
# HELPER: GET CURRENT FARMER
# =========================================================

def get_current_farmer(
    current_user: User,
    db: Session,
) -> Farmer:

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

    return farmer


# =========================================================
# HELPER: GET CURRENT EXPERT
# =========================================================

def get_current_expert(
    current_user: User,
    db: Session,
) -> Expert:

    expert = (
        db.query(Expert)
        .filter(Expert.user_id == current_user.user_id)
        .first()
    )

    if not expert:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذه الميزة متاحة للخبراء فقط"
        )

    return expert


# =========================================================
# CREATE CONSULTATION
# Farmer sends consultation request to expert
# =========================================================

@router.post(
    "",
    response_model=ConsultationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_consultation(
    payload: ConsultationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # -----------------------------------------------------
    # 1. Get farmer from logged-in user
    # -----------------------------------------------------

    farmer = get_current_farmer(
        current_user=current_user,
        db=db,
    )

    # -----------------------------------------------------
    # 2. Check expert
    # -----------------------------------------------------

    expert = (
        db.query(Expert)
        .filter(Expert.expert_id == payload.expert_id)
        .first()
    )

    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الخبير غير موجود"
        )

    # -----------------------------------------------------
    # 3. Check expert availability
    # -----------------------------------------------------

    if not expert.is_available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="الخبير غير متاح حالياً لاستقبال استشارات جديدة"
        )

    # -----------------------------------------------------
    # 4. Validate AI diagnosis if provided
    # -----------------------------------------------------

    if payload.ai_diagnosis_id is not None:

        ai_diagnosis = (
            db.query(Diagnosis)
            .filter(
                Diagnosis.diagnosis_id == payload.ai_diagnosis_id,
                Diagnosis.farmer_id == farmer.farmer_id,
                Diagnosis.source == DiagnosisSource.AI,
            )
            .first()
        )

        if not ai_diagnosis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="تشخيص الذكاء الاصطناعي غير موجود أو لا يخص هذا المزارع"
            )

    # -----------------------------------------------------
    # 5. Create consultation
    # -----------------------------------------------------

    new_consultation = Consultation(
        farmer_id=farmer.farmer_id,
        expert_id=expert.expert_id,
        ai_diagnosis_id=payload.ai_diagnosis_id,
        expert_diagnosis_id=None,
        status=ConsultationStatus.PENDING_EXPERT,
        questions_used=0,
        max_questions=3,
    )

    db.add(new_consultation)
    db.commit()
    db.refresh(new_consultation)

    return new_consultation


# =========================================================
# GET FARMER CONSULTATIONS
# Farmer views his consultations
# =========================================================

@router.get(
    "/farmer/my",
    response_model=list[ConsultationOut],
)
def get_my_farmer_consultations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = get_current_farmer(
        current_user=current_user,
        db=db,
    )

    consultations = (
        db.query(Consultation)
        .filter(
            Consultation.farmer_id == farmer.farmer_id
        )
        .order_by(
            Consultation.created_at.desc()
        )
        .all()
    )

    return consultations


# =========================================================
# GET EXPERT CONSULTATIONS
# Expert views consultation requests/history
# =========================================================

@router.get(
    "/expert/my",
    response_model=list[ConsultationOut],
)
def get_my_expert_consultations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    expert = get_current_expert(
        current_user=current_user,
        db=db,
    )

    consultations = (
        db.query(Consultation)
        .filter(
            Consultation.expert_id == expert.expert_id
        )
        .order_by(
            Consultation.created_at.desc()
        )
        .all()
    )

    return consultations


# =========================================================
# EXPERT ACCEPT CONSULTATION
# PENDING_EXPERT -> PENDING_PAYMENT
# =========================================================

@router.patch(
    "/{consultation_id}/accept",
    response_model=ConsultationOut,
)
def accept_consultation(
    consultation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    expert = get_current_expert(
        current_user=current_user,
        db=db,
    )

    # -----------------------------------------------------
    # 1. Get consultation belonging to this expert
    # -----------------------------------------------------

    consultation = (
        db.query(Consultation)
        .filter(
            Consultation.consultation_id == consultation_id,
            Consultation.expert_id == expert.expert_id,
        )
        .first()
    )

    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="طلب الاستشارة غير موجود"
        )

    # -----------------------------------------------------
    # 2. Only pending requests can be accepted
    # -----------------------------------------------------

    if consultation.status != ConsultationStatus.PENDING_EXPERT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="لا يمكن قبول هذه الاستشارة في حالتها الحالية"
        )

    # -----------------------------------------------------
    # 3. Accept consultation
    # -----------------------------------------------------

    consultation.status = ConsultationStatus.PENDING_PAYMENT
    consultation.accepted_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(consultation)

    return consultation


# =========================================================
# EXPERT REJECT CONSULTATION
# PENDING_EXPERT -> REJECTED
# =========================================================

@router.patch(
    "/{consultation_id}/reject",
    response_model=ConsultationOut,
)
def reject_consultation(
    consultation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    expert = get_current_expert(
        current_user=current_user,
        db=db,
    )

    # -----------------------------------------------------
    # 1. Get consultation belonging to this expert
    # -----------------------------------------------------

    consultation = (
        db.query(Consultation)
        .filter(
            Consultation.consultation_id == consultation_id,
            Consultation.expert_id == expert.expert_id,
        )
        .first()
    )

    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="طلب الاستشارة غير موجود"
        )

    # -----------------------------------------------------
    # 2. Only pending requests can be rejected
    # -----------------------------------------------------

    if consultation.status != ConsultationStatus.PENDING_EXPERT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="لا يمكن رفض هذه الاستشارة في حالتها الحالية"
        )

    # -----------------------------------------------------
    # 3. Reject consultation
    # -----------------------------------------------------

    consultation.status = ConsultationStatus.REJECTED

    db.commit()
    db.refresh(consultation)

    return consultation