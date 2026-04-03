from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.delivery_point import DeliveryPoint
from app.schemas.delivery_point import DeliveryPointCreate


def list_delivery_points(db: Session) -> list[DeliveryPoint]:
    return db.query(DeliveryPoint).order_by(DeliveryPoint.building, DeliveryPoint.name).all()


def create_delivery_point(db: Session, payload: DeliveryPointCreate) -> DeliveryPoint:
    point = DeliveryPoint(**payload.model_dump())
    db.add(point)
    db.commit()
    db.refresh(point)
    return point


def delete_delivery_point(db: Session, point_id: int) -> None:
    point = db.query(DeliveryPoint).filter(DeliveryPoint.id == point_id).first()
    if not point:
        raise HTTPException(status_code=404, detail="Delivery point not found")
    db.delete(point)
    db.commit()