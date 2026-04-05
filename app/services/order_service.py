from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.delivery_point import DeliveryPoint
from app.models.menu_item import MenuItem
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.services.canteen_service import get_canteen_by_owner
from app.services.notification_service import create_notification


def _get_order_or_404(db: Session, order_id: int) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _assert_order_access(order: Order, current_user: User):
    if (
        order.user_id != current_user.id
        and current_user.role not in (UserRole.canteen, UserRole.admin)
    ):
        raise HTTPException(status_code=403, detail="Access denied")


# ── Valid status transitions ────────────────────────────────────────────────
VALID_TRANSITIONS: dict[OrderStatus, list[OrderStatus]] = {
    OrderStatus.pending:    [OrderStatus.confirmed, OrderStatus.cancelled],
    OrderStatus.confirmed:  [OrderStatus.preparing, OrderStatus.cancelled],
    OrderStatus.preparing:  [OrderStatus.delivering],
    OrderStatus.delivering: [OrderStatus.delivered],
    OrderStatus.delivered:  [],
    OrderStatus.cancelled:  [],
}

STATUS_MESSAGES: dict[OrderStatus, str] = {
    OrderStatus.confirmed:  "Pesananmu telah dikonfirmasi oleh kantin.",
    OrderStatus.preparing:  "Kantin sedang menyiapkan pesananmu.",
    OrderStatus.delivering: "Pesananmu sedang dalam perjalanan ke titik antar.",
    OrderStatus.delivered:  "Pesananmu telah tiba! Selamat makan.",
    OrderStatus.cancelled:  "Pesananmu telah dibatalkan.",
}


def create_order(db: Session, payload: OrderCreate, current_user: User) -> Order:
    # Validate canteen
    from app.models.canteen import Canteen
    canteen = db.query(Canteen).filter(Canteen.id == payload.canteen_id).first()
    if not canteen:
        raise HTTPException(status_code=404, detail="Canteen not found")
    if not canteen.is_open:
        raise HTTPException(status_code=400, detail="Canteen is currently closed")

    # Validate delivery point
    delivery_point = db.query(DeliveryPoint).filter(
        DeliveryPoint.id == payload.delivery_point_id
    ).first()
    if not delivery_point:
        raise HTTPException(status_code=404, detail="Delivery point not found")

    # Validate & price each item
    total = 0.0
    order_items: list[OrderItem] = []
    for item_data in payload.items:
        if item_data.quantity < 1:
            raise HTTPException(
                status_code=400,
                detail=f"Quantity for item {item_data.menu_item_id} must be at least 1",
            )
        menu_item = db.query(MenuItem).filter(
            MenuItem.id == item_data.menu_item_id,
            MenuItem.canteen_id == payload.canteen_id,
            MenuItem.is_available == True,
        ).first()
        if not menu_item:
            raise HTTPException(
                status_code=404,
                detail=f"Menu item {item_data.menu_item_id} not found or unavailable",
            )
        subtotal = round(menu_item.price * item_data.quantity, 2)
        total += subtotal
        order_items.append(
            OrderItem(
                menu_item_id=menu_item.id,
                quantity=item_data.quantity,
                subtotal=subtotal,
                notes=item_data.notes,
            )
        )

    order = Order(
        user_id=current_user.id,
        canteen_id=payload.canteen_id,
        delivery_point_id=payload.delivery_point_id,
        total_price=round(total, 2),
        notes=payload.notes,
        items=order_items,
    )
    db.add(order)
    db.flush()  # get order.id before commit

    create_notification(
        db,
        user_id=current_user.id,
        order_id=order.id,
        title="Pesanan masuk",
        message=(
            f"Pesanan #{order.id} dari {canteen.name} "
            f"ke {delivery_point.name} sedang menunggu konfirmasi."
        ),
    )

    # Also notify canteen owner
    create_notification(
        db,
        user_id=canteen.user_id,
        order_id=order.id,
        title="Pesanan baru masuk",
        message=f"Ada pesanan baru #{order.id} dari {current_user.name}.",
    )

    db.commit()
    db.refresh(order)
    return order


def get_my_orders(db: Session, current_user: User) -> list[Order]:
    return (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.ordered_at.desc())
        .all()
    )


def get_canteen_orders(
    db: Session,
    current_user: User,
    status_filter: OrderStatus | None = None,
) -> list[Order]:
    canteen = get_canteen_by_owner(db, current_user.id)
    query = db.query(Order).filter(Order.canteen_id == canteen.id)
    if status_filter:
        query = query.filter(Order.status == status_filter)
    return query.order_by(Order.ordered_at.desc()).all()


def get_order_detail(db: Session, order_id: int, current_user: User) -> Order:
    order = _get_order_or_404(db, order_id)
    _assert_order_access(order, current_user)
    return order


def update_order_status(
    db: Session,
    order_id: int,
    payload: OrderStatusUpdate,
    current_user: User,
) -> Order:
    order = _get_order_or_404(db, order_id)

    # Validate transition
    allowed = VALID_TRANSITIONS.get(order.status, [])
    if payload.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot transition from '{order.status.value}' "
                f"to '{payload.status.value}'. "
                f"Allowed: {[s.value for s in allowed] or 'none'}"
            ),
        )

    order.status = payload.status
    if payload.status == OrderStatus.delivered:
        order.delivered_at = datetime.utcnow()

    msg = STATUS_MESSAGES.get(payload.status, f"Status: {payload.status.value}")
    create_notification(
        db,
        user_id=order.user_id,
        order_id=order.id,
        title="Status pesanan diperbarui",
        message=msg,
    )

    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order_id: int, current_user: User) -> Order:
    order = _get_order_or_404(db, order_id)
    _assert_order_access(order, current_user)

    if OrderStatus.cancelled not in VALID_TRANSITIONS.get(order.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Order with status '{order.status.value}' cannot be cancelled",
        )

    order.status = OrderStatus.cancelled
    create_notification(
        db,
        user_id=order.user_id,
        order_id=order.id,
        title="Pesanan dibatalkan",
        message=f"Pesanan #{order.id} telah dibatalkan.",
    )
    db.commit()
    db.refresh(order)
    return order

def confirm_and_cook(db: Session, order_id: int, current_user: User) -> Order:
    order = _get_order_or_404(db, order_id)

    if order.status != OrderStatus.pending:
        raise HTTPException(
            status_code=400,
            detail=f"Order harus dalam status 'pending', sekarang '{order.status.value}'"
        )

    # Skip confirmed, langsung ke preparing
    order.status = OrderStatus.preparing

    create_notification(
        db,
        user_id=order.user_id,
        order_id=order.id,
        title="Pesanan dikonfirmasi & dimasak",
        message="Kantin telah mengkonfirmasi pesananmu dan sedang memasaknya.",
    )

    db.commit()
    db.refresh(order)
    return order
