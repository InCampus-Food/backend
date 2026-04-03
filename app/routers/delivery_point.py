from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.delivery_point import DeliveryPoint
from app.models.user import User, UserRole
from app.schemas.delivery_point import DeliveryPointCreate, DeliveryPointResponse

router = APIRouter(prefix="/delivery-points", tags=["Delivery Points"])


@router.get("", response_model=List[DeliveryPointResponse])
def list_delivery_points(db: Session = Depends(get_db)):
    return db.query(DeliveryPoint).all()


@router.post("", response_model=DeliveryPointResponse, status_code=status.HTTP_201_CREATED)
def create_delivery_point(
    payload: DeliveryPointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    point = DeliveryPoint(**payload.model_dump())
    db.add(point)
    db.commit()
    db.refresh(point)
    return point


@router.delete("/{point_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_delivery_point(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    point = db.query(DeliveryPoint).filter(DeliveryPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="Delivery point not found")
    db.delete(point)
    db.commit()
