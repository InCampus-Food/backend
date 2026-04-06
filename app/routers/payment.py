from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentResponse, MidtransWebhookPayload
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=PaymentResponse)
async def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await payment_service.create_payment(db, payload, current_user)


@router.get("/{order_id}", response_model=PaymentResponse)
def get_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return payment_service.get_payment_by_order(db, order_id, current_user)


@router.post("/webhook/midtrans")
async def midtrans_webhook(
    payload: MidtransWebhookPayload,
    db: Session = Depends(get_db),
):
    await payment_service.handle_midtrans_webhook(db, payload)
    return {"status": "ok"}
