from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.payment import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    order_id: int
    method: PaymentMethod


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    method: PaymentMethod
    status: PaymentStatus
    amount: float
    snap_token: Optional[str]
    payment_url: Optional[str]
    expired_at: Optional[datetime]
    paid_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class MidtransWebhookPayload(BaseModel):
    order_id: str
    transaction_status: str
    fraud_status: Optional[str] = None
    payment_type: Optional[str] = None
    gross_amount: Optional[str] = None
