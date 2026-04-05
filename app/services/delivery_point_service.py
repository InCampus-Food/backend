from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.delivery_point import DeliveryPoint
from app.schemas.delivery_point import DeliveryPointCreate, DeliveryPointUpdate


def get_user_delivery_points(db: Session, user_id: int) -> list[DeliveryPoint]:
    return (
        db.query(DeliveryPoint)
        .filter(DeliveryPoint.user_id == user_id)
        .order_by(DeliveryPoint.is_default.desc(), DeliveryPoint.id.desc())
        .all()
    )


def _get_or_404(db: Session, point_id: int, user_id: int) -> DeliveryPoint:
    point = db.query(DeliveryPoint).filter(
        DeliveryPoint.id == point_id,
        DeliveryPoint.user_id == user_id,
    ).first()
    if not point:
        raise HTTPException(status_code=404, detail="Delivery point not found")
    return point


def create_delivery_point(db: Session, payload: DeliveryPointCreate, user_id: int) -> DeliveryPoint:
    # Kalau is_default, unset default yang lain
    if payload.is_default:
        db.query(DeliveryPoint).filter(
            DeliveryPoint.user_id == user_id,
            DeliveryPoint.is_default == True,
        ).update({"is_default": False})

    point = DeliveryPoint(**payload.model_dump(), user_id=user_id)

    # Auto set default kalau ini pertama
    count = db.query(DeliveryPoint).filter(DeliveryPoint.user_id == user_id).count()
    if count == 0:
        point.is_default = True

    db.add(point)
    db.commit()
    db.refresh(point)
    return point


def update_delivery_point(db: Session, point_id: int, payload: DeliveryPointUpdate, user_id: int) -> DeliveryPoint:
    point = _get_or_404(db, point_id, user_id)

    if payload.is_default:
        db.query(DeliveryPoint).filter(
            DeliveryPoint.user_id == user_id,
            DeliveryPoint.is_default == True,
        ).update({"is_default": False})

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(point, field, value)

    db.commit()
    db.refresh(point)
    return point


def delete_delivery_point(db: Session, point_id: int, user_id: int) -> None:
    point = _get_or_404(db, point_id, user_id)
    db.delete(point)
    db.commit()


def set_default_delivery_point(db: Session, point_id: int, user_id: int) -> DeliveryPoint:
    db.query(DeliveryPoint).filter(
        DeliveryPoint.user_id == user_id,
        DeliveryPoint.is_default == True,
    ).update({"is_default": False})

    point = _get_or_404(db, point_id, user_id)
    point.is_default = True
    db.commit()
    db.refresh(point)
    return point
