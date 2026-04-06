import uuid
from datetime import datetime, timedelta

import midtransclient
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.websocket import ws_manager
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.user import User
from app.schemas.payment import PaymentCreate, MidtransWebhookPayload
from app.services.notification_service import create_notification


def _get_snap_client():
    return midtransclient.Snap(
        is_production=settings.MIDTRANS_IS_PRODUCTION,
        server_key=settings.MIDTRANS_SERVER_KEY,
        client_key=settings.MIDTRANS_CLIENT_KEY,
    )


async def create_payment(db: Session, payload: PaymentCreate, current_user: User) -> Payment:
    order = db.query(Order).filter(Order.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your order")
    if order.status == OrderStatus.cancelled:
        raise HTTPException(status_code=400, detail="Cannot pay for a cancelled order")
    if order.payment:
        raise HTTPException(status_code=400, detail="Order already has a payment")

    # COD — langsung pending
    if payload.method == PaymentMethod.cod:
        payment = Payment(
            order_id=order.id,
            method=PaymentMethod.cod,
            amount=order.total_price,
            status=PaymentStatus.paid,
            paid_at=datetime.utcnow(),
        )
        order.status = OrderStatus.pending
        db.add(payment)
        create_notification(
            db,
            user_id=current_user.id,
            order_id=order.id,
            title="Pesanan dikonfirmasi",
            message=f"Pesanan #{order.id} akan dibayar tunai saat tiba.",
        )
        db.commit()
        db.refresh(payment)
        return payment

    # Midtrans — buat snap token
    midtrans_order_id = f"INCAMPUS-{order.id}-{uuid.uuid4().hex[:8].upper()}"
    expired_at = datetime.utcnow() + timedelta(minutes=10)

    snap = _get_snap_client()
    transaction = snap.create_transaction({
        "transaction_details": {
            "order_id": midtrans_order_id,
            "gross_amount": int(order.total_price),
        },
        "item_details": [
            {
                "id": str(item.menu_item_id),
                "price": int(item.menu_item.price),
                "quantity": item.quantity,
                "name": item.menu_item.name[:50],
            }
            for item in order.items
        ],
        "customer_details": {
            "first_name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone or "08000000000",
        },
        "expiry": {
            "unit": "minutes",
            "duration": 10,
        },
    })

    payment = Payment(
        order_id=order.id,
        method=PaymentMethod.midtrans,
        amount=order.total_price,
        status=PaymentStatus.pending,
        snap_token=transaction["token"],
        payment_url=transaction["redirect_url"],
        midtrans_order_id=midtrans_order_id,
        expired_at=expired_at,
    )
    order.status = OrderStatus.waiting_for_payment
    db.add(payment)

    create_notification(
        db,
        user_id=current_user.id,
        order_id=order.id,
        title="Menunggu pembayaran",
        message=f"Selesaikan pembayaran pesanan #{order.id} dalam 10 menit.",
    )

    db.commit()
    db.refresh(payment)
    return payment


async def handle_midtrans_webhook(db: Session, payload: MidtransWebhookPayload):
    payment = db.query(Payment).filter(
        Payment.midtrans_order_id == payload.order_id
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    order = payment.order
    transaction_status = payload.transaction_status
    fraud_status = payload.fraud_status

    if transaction_status == "capture":
        if fraud_status == "accept":
            payment.status = PaymentStatus.paid
            payment.paid_at = datetime.utcnow()
            order.status = OrderStatus.pending
    elif transaction_status == "settlement":
        payment.status = PaymentStatus.paid
        payment.paid_at = datetime.utcnow()
        order.status = OrderStatus.pending
    elif transaction_status in ("cancel", "deny", "expire"):
        payment.status = PaymentStatus.expired if transaction_status == "expire" else PaymentStatus.failed
        order.status = OrderStatus.cancelled
    elif transaction_status == "pending":
        payment.status = PaymentStatus.pending

    db.commit()

    # Push via WebSocket ke user
    await ws_manager.send_to_user(str(order.user_id), {
        "type": "payment_update",
        "order_id": order.id,
        "order_status": order.status.value,
        "payment_status": payment.status.value,
    })

    # Notifikasi
    if payment.status == PaymentStatus.paid:
        create_notification(
            db,
            user_id=order.user_id,
            order_id=order.id,
            title="Pembayaran berhasil!",
            message=f"Pembayaran pesanan #{order.id} sebesar Rp{payment.amount:,.0f} berhasil.",
        )
        db.commit()


async def expire_pending_payments(db: Session):
    """Dipanggil oleh background task — cancel order yang timeout"""
    now = datetime.utcnow()
    expired = db.query(Payment).filter(
        Payment.status == PaymentStatus.pending,
        Payment.expired_at <= now,
        Payment.method == PaymentMethod.midtrans,
    ).all()

    for payment in expired:
        payment.status = PaymentStatus.expired
        payment.order.status = OrderStatus.cancelled
        await ws_manager.send_to_user(str(payment.order.user_id), {
            "type": "payment_expired",
            "order_id": payment.order_id,
            "order_status": "cancelled",
        })

    if expired:
        db.commit()


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
