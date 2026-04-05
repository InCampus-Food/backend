from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.delivery_point import DeliveryPointCreate, DeliveryPointUpdate, DeliveryPointResponse
from app.services import delivery_point_service

router = APIRouter(prefix="/delivery-points", tags=["Delivery Points"])


@router.get("", response_model=List[DeliveryPointResponse])
def list_my_delivery_points(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return delivery_point_service.get_user_delivery_points(db, current_user.id)


@router.post("", response_model=DeliveryPointResponse, status_code=status.HTTP_201_CREATED)
def create_delivery_point(
    payload: DeliveryPointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return delivery_point_service.create_delivery_point(db, payload, current_user.id)


@router.patch("/{point_id}", response_model=DeliveryPointResponse)
def update_delivery_point(
    point_id: int,
    payload: DeliveryPointUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return delivery_point_service.update_delivery_point(db, point_id, payload, current_user.id)


@router.delete("/{point_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_delivery_point(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delivery_point_service.delete_delivery_point(db, point_id, current_user.id)


@router.patch("/{point_id}/set-default", response_model=DeliveryPointResponse)
def set_default(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return delivery_point_service.set_default_delivery_point(db, point_id, current_user.id)
