from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.canteen import Canteen
from app.models.user import User, UserRole
from app.schemas.canteen import CanteenCreate, CanteenUpdate


def get_all_open_canteens(db: Session) -> list[Canteen]:
    return db.query(Canteen).filter(Canteen.is_open == True).all()


def get_canteen_by_id(db: Session, canteen_id: int) -> Canteen:
    canteen = db.query(Canteen).filter(Canteen.id == canteen_id).first()
    if not canteen:
        raise HTTPException(status_code=404, detail="Canteen not found")
    return canteen


def get_canteen_by_owner(db: Session, user_id: int):
    from fastapi import HTTPException
    canteen = db.query(Canteen).filter(Canteen.user_id == user_id).first()
    if not canteen:
        raise HTTPException(status_code=404, detail="Canteen not found")
    return canteen


def create_canteen(db: Session, payload: CanteenCreate, owner: User) -> Canteen:
    existing = db.query(Canteen).filter(Canteen.user_id == owner.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a canteen",
        )
    canteen = Canteen(**payload.model_dump(), user_id=owner.id)
    db.add(canteen)
    db.commit()
    db.refresh(canteen)
    return canteen


def update_canteen(
    db: Session,
    canteen_id: int,
    payload: CanteenUpdate,
    current_user: User,
) -> Canteen:
    canteen = get_canteen_by_id(db, canteen_id)
    if canteen.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not your canteen")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(canteen, field, value)
    db.commit()
    db.refresh(canteen)
    return canteen


def toggle_canteen_status(db: Session, canteen_id: int, current_user: User) -> Canteen:
    canteen = get_canteen_by_id(db, canteen_id)
    if canteen.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not your canteen")
    canteen.is_open = not canteen.is_open
    db.commit()
    db.refresh(canteen)
    return canteen
