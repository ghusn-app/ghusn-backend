from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user

from app.models.user import User
from app.models.farmer import Farmer
from app.models.expert import Expert
from app.models.consultation import Consultation, ConsultationStatus
from app.models.payments import Payment, PaymentStatus

from app.schemas.payment import PaymentCreate, PaymentOut


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
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
# CREATE PAYMENT
# =========================================================

@router.post(
    "",
    response_model=PaymentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    payload: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # -----------------------------------------------------
    # 1. Get current farmer
    # -----------------------------------------------------

    farmer = get_current_farmer(
        current_user=current_user,
        db=db,
    )

    # -----------------------------------------------------
    # 2. Get consultation
    # -----------------------------------------------------

    consultation = (
        db.query(Consultation)
        .filter(
            Consultation.consultation_id == payload.consultation_id,
            Consultation.farmer_id == farmer.farmer_id,
        )
        .first()
    )

    if not consultation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الاستشارة غير موجودة أو لا تخص هذا المزارع"
        )

    # -----------------------------------------------------
    # 3. Consultation must be waiting for payment
    # -----------------------------------------------------

    if consultation.status != ConsultationStatus.PENDING_PAYMENT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="الاستشارة ليست بانتظار الدفع"
        )

    # -----------------------------------------------------
    # 4. Get expert
    # -----------------------------------------------------

    expert = (
        db.query(Expert)
        .filter(
            Expert.expert_id == consultation.expert_id
        )
        .first()
    )

    if not expert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الخبير المرتبط بالاستشارة غير موجود"
        )

    # -----------------------------------------------------
    # 5. Prevent payment if already paid
    # -----------------------------------------------------

    paid_payment = (
        db.query(Payment)
        .filter(
            Payment.consultation_id == consultation.consultation_id,
            Payment.status == PaymentStatus.PAID,
        )
        .first()
    )

    if paid_payment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="تم دفع هذه الاستشارة مسبقاً"
        )

    # -----------------------------------------------------
    # 6. Check for existing pending payment
    # -----------------------------------------------------

    pending_payment = (
        db.query(Payment)
        .filter(
            Payment.consultation_id == consultation.consultation_id,
            Payment.status == PaymentStatus.PENDING,
        )
        .first()
    )

    if pending_payment:
        return pending_payment

    # -----------------------------------------------------
    # 7. Create payment
    # -----------------------------------------------------

    new_payment = Payment(
        consultation_id=consultation.consultation_id,
        farmer_id=farmer.farmer_id,

        # Price comes from expert profile
        # Never trust amount from frontend
        amount=expert.consultation_price,

        currency="ILS",

        status=PaymentStatus.PENDING,

        # Jawwal Pay will be the payment provider
        payment_method="jawwal_pay",

        # Will be added after real payment
        transaction_id=None,
        paid_at=None,
    )

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    return new_payment


# =========================================================
# GET MY PAYMENTS
# =========================================================

@router.get(
    "/my",
    response_model=list[PaymentOut],
)
def get_my_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = get_current_farmer(
        current_user=current_user,
        db=db,
    )

    payments = (
        db.query(Payment)
        .filter(
            Payment.farmer_id == farmer.farmer_id
        )
        .order_by(
            Payment.created_at.desc()
        )
        .all()
    )

    return payments


# =========================================================
# GET PAYMENT BY ID
# =========================================================

@router.get(
    "/{payment_id}",
    response_model=PaymentOut,
)
def get_payment_by_id(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    farmer = get_current_farmer(
        current_user=current_user,
        db=db,
    )

    payment = (
        db.query(Payment)
        .filter(
            Payment.payment_id == payment_id,
            Payment.farmer_id == farmer.farmer_id,
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="عملية الدفع غير موجودة"
        )

    return payment