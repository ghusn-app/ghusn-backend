from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user

from app.models.user import User, UserRole
from app.models.expert import Expert

from app.schemas.expert import ExpertOut,ExpertUpdate,ExpertAvailabilityUpdate

router = APIRouter(
    prefix="/experts",
    tags=["Experts"]
)


# =========================================================
# HELPER - GET CURRENT EXPERT
# =========================================================

def get_current_expert(
    current_user: User,
    db: Session,
):
    # User must have EXPERT role
    if current_user.role != UserRole.EXPERT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذه الميزة متاحة للخبراء فقط"
        )

    expert = (
        db.query(Expert)
        .filter(Expert.user_id == current_user.user_id)
        .first()
    )

    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ملف الخبير غير موجود"
        )

    return expert


# =========================================================
# GET CURRENT EXPERT PROFILE
# =========================================================

@router.get(
    "/me",
    response_model=ExpertOut
)
def get_my_expert_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    expert = get_current_expert(
        current_user=current_user,
        db=db
    )

    return expert


# =========================================================
# UPDATE CURRENT EXPERT PROFILE
# =========================================================

@router.patch(
    "/me",
    response_model=ExpertOut
)
def update_my_expert_profile(
    payload: ExpertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    expert = get_current_expert(
        current_user=current_user,
        db=db
    )

    # Only update fields sent by frontend
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(expert, field, value)

    db.commit()
    db.refresh(expert)

    return expert


# =========================================================
# UPDATE EXPERT AVAILABILITY
# =========================================================

@router.patch(
    "/me/availability",
    response_model=ExpertOut
)
def update_my_availability(
    payload: ExpertAvailabilityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    expert = get_current_expert(
        current_user=current_user,
        db=db
    )

    expert.is_available = payload.is_available

    db.commit()
    db.refresh(expert)

    return expert


# =========================================================
# GET AVAILABLE EXPERTS
# =========================================================

@router.get(
    "",
    response_model=list[ExpertOut]
)
def get_available_experts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    experts = (
        db.query(Expert)
        .filter(Expert.is_available.is_(True))
        .order_by(Expert.created_at.desc())
        .all()
    )

    return experts


# =========================================================
# GET EXPERT BY ID
# =========================================================

@router.get(
    "/{expert_id}",
    response_model=ExpertOut
)
def get_expert_by_id(
    expert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    expert = (
        db.query(Expert)
        .filter(
            Expert.expert_id == expert_id,
            Expert.is_available.is_(True)
        )
        .first()
    )

    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الخبير غير موجود أو غير متاح حالياً"
        )

    return expert