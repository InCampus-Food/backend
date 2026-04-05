from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.order import OrderStatus
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.create_order(db, payload, current_user)


@router.get("/me", response_model=List[OrderResponse])
def my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.get_my_orders(db, current_user)


@router.get("/canteen", response_model=List[OrderResponse])
def canteen_orders(
    status_filter: Optional[OrderStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.canteen, UserRole.admin)),
):
    return order_service.get_canteen_orders(db, current_user, status_filter)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.get_order_detail(db, order_id, current_user)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.canteen, UserRole.admin)),
):
    return order_service.update_order_status(db, order_id, payload, current_user)


@router.patch("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.cancel_order(db, order_id, current_user)

@router.post("/{order_id}/confirm-and-cook", response_model=OrderResponse)
async def confirm_and_cook(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.canteen, UserRole.admin)),
):
    return order_service.confirm_and_cook(db, order_id, current_user)
