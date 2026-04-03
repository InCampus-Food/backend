import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentCreate
from app.services.notification_service import create_notification


def process_payment(db: Session, payload: PaymentCreate, current_user: User) -> Payment:
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your order")
    if order.status == OrderStatus.cancelled:
        raise HTTPException(status_code=400, detail="Cannot pay for a cancelled order")
    if order.payment:
        raise HTTPException(status_code=400, detail="Order already has a payment")
    if round(payload.amount, 2) != round(order.total_price, 2):
        raise HTTPException(
            status_code=400,
            detail=f"Amount mismatch. Expected {order.total_price}, got {payload.amount}",
        )

    payment = Payment(
        order_id=order.id,
        method=payload.method,
        amount=payload.amount,
        ref_code=str(uuid.uuid4()),
        status=PaymentStatus.paid,
        paid_at=datetime.utcnow(),
    )
    order.status = OrderStatus.confirmed
    db.add(payment)

    create_notification(
        db,
        user_id=current_user.id,
        order_id=order.id,
        title="Pembayaran berhasil",
        message=(
            f"Pembayaran pesanan #{order.id} sebesar "
            f"Rp{payload.amount:,.0f} berhasil diterima."
        ),
    )

    db.commit()
    db.refresh(payment)
    return payment


def get_payment_by_order(db: Session, order_id: int, current_user: User) -> Payment:
    from app.models.user import UserRole
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if (
        order.user_id != current_user.id
        and current_user.role not in (UserRole.canteen, UserRole.admin)
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    if not order.payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return order.payment