from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user

from app.models.user import User
from app.models.farmer import Farmer
from app.models.expert import Expert
from app.models.consultation import Consultation, ConsultationStatus
from app.models.consultation_message import ConsultationMessage

from app.schemas.consultation_message import (
    ConsultationMessageCreate,
    ConsultationMessageOut,
)


router = APIRouter(
    prefix="/consultations",
    tags=["Consultation Messages"]
)


# =========================================================
# GET CONSULTATION MESSAGES
# =========================================================

@router.get(
    "/{consultation_id}/messages",
    response_model=list[ConsultationMessageOut]
)
def get_consultation_messages(
    consultation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # 1. Get consultation
    consultation = (
        db.query(Consultation)
        .filter(
            Consultation.consultation_id == consultation_id
        )
        .first()
    )

    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الاستشارة غير موجودة"
        )

    # 2. Check if current user is the farmer
    farmer = (
        db.query(Farmer)
        .filter(
            Farmer.user_id == current_user.user_id
        )
        .first()
    )

    is_consultation_farmer = (
        farmer is not None
        and farmer.farmer_id == consultation.farmer_id
    )

    # 3. Check if current user is the expert
    expert = (
        db.query(Expert)
        .filter(
            Expert.user_id == current_user.user_id
        )
        .first()
    )

    is_consultation_expert = (
        expert is not None
        and expert.expert_id == consultation.expert_id
    )

    # 4. Check permission
    if not is_consultation_farmer and not is_consultation_expert:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحية لعرض هذه المحادثة"
        )

    # 5. Get messages
    messages = (
        db.query(ConsultationMessage)
        .filter(
            ConsultationMessage.consultation_id
            == consultation.consultation_id
        )
        .order_by(
            ConsultationMessage.created_at.asc()
        )
        .all()
    )

    return messages


# =========================================================
# SEND CONSULTATION MESSAGE
# =========================================================

@router.post(
    "/{consultation_id}/messages",
    response_model=ConsultationMessageOut,
    status_code=status.HTTP_201_CREATED,
)
def send_consultation_message(
    consultation_id: int,
    payload: ConsultationMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # 1. Get consultation
    consultation = (
        db.query(Consultation)
        .filter(
            Consultation.consultation_id == consultation_id
        )
        .first()
    )

    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الاستشارة غير موجودة"
        )

    # 2. Get current farmer
    farmer = (
        db.query(Farmer)
        .filter(
            Farmer.user_id == current_user.user_id
        )
        .first()
    )

    is_consultation_farmer = (
        farmer is not None
        and farmer.farmer_id == consultation.farmer_id
    )

    # 3. Get current expert
    expert = (
        db.query(Expert)
        .filter(
            Expert.user_id == current_user.user_id
        )
        .first()
    )

    is_consultation_expert = (
        expert is not None
        and expert.expert_id == consultation.expert_id
    )

    # 4. Check permission
    if not is_consultation_farmer and not is_consultation_expert:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحية لإرسال رسالة في هذه الاستشارة"
        )

    # 5. Chat must be available
    if consultation.status not in (
        ConsultationStatus.OPEN,
        ConsultationStatus.WAITING_EXPERT,
        ConsultationStatus.WAITING_FARMER,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="المحادثة غير متاحة في حالة الاستشارة الحالية"
        )

    # =====================================================
    # 6. FARMER SENDS A MESSAGE
    # =====================================================

    if is_consultation_farmer:

        # Farmer can send first question when OPEN,
        # or next question after expert replies.
        if consultation.status not in (
            ConsultationStatus.OPEN,
            ConsultationStatus.WAITING_FARMER,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="يجب انتظار رد الخبير قبل إرسال سؤال جديد"
            )

        # Maximum 3 questions
        if consultation.questions_used >= consultation.max_questions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="تم استخدام الحد الأقصى لأسئلة الاستشارة"
            )

        new_message = ConsultationMessage(
            consultation_id=consultation.consultation_id,
            sender_id=current_user.user_id,
            message=payload.message,
            image_url=None,
        )

        db.add(new_message)

        # Count farmer questions only
        consultation.questions_used += 1

        # Now expert must reply
        consultation.status = ConsultationStatus.WAITING_EXPERT

        db.commit()
        db.refresh(new_message)

        return new_message

    # =====================================================
    # 7. EXPERT SENDS A MESSAGE
    # =====================================================

    if is_consultation_expert:

        # Expert can reply only after farmer sends a question
        if consultation.status != ConsultationStatus.WAITING_EXPERT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="لا يوجد سؤال من المزارع بانتظار الرد"
            )

        new_message = ConsultationMessage(
            consultation_id=consultation.consultation_id,
            sender_id=current_user.user_id,
            message=payload.message,
            image_url=None,
        )

        db.add(new_message)

        # If expert answered question 3,
        # consultation is finished.
        if consultation.questions_used >= consultation.max_questions:
            consultation.status = ConsultationStatus.CLOSED
        else:
            consultation.status = ConsultationStatus.WAITING_FARMER

        db.commit()
        db.refresh(new_message)

        return new_message