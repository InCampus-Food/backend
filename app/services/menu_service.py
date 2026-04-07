from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem
from app.models.user import User, UserRole
from app.schemas.menu_item import MenuItemCreate, MenuItemUpdate
from app.services.canteen_service import get_canteen_by_id


def _assert_canteen_owner(canteen, current_user: User):
    if canteen.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not your canteen")


def list_menu_items(
    db: Session,
    canteen_id: int,
    category: str | None = None,
    include_unavailable: bool = False,
) -> list[MenuItem]:
    get_canteen_by_id(db, canteen_id)
    query = db.query(MenuItem).filter(MenuItem.canteen_id == canteen_id)
    if not include_unavailable:
        query = query.filter(MenuItem.is_available == True)
    if category:
        query = query.filter(MenuItem.category == category)
    return query.all()


def get_menu_item(db: Session, canteen_id: int, item_id: int) -> MenuItem:
    item = db.query(MenuItem).filter(
        MenuItem.id == item_id,
        MenuItem.canteen_id == canteen_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item


def create_menu_item(
    db: Session,
    canteen_id: int,
    payload: MenuItemCreate,
    current_user: User,
) -> MenuItem:
    canteen = get_canteen_by_id(db, canteen_id)
    _assert_canteen_owner(canteen, current_user)
    item = MenuItem(**payload.model_dump(), canteen_id=canteen_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_menu_item(
    db: Session,
    canteen_id: int,
    item_id: int,
    payload: MenuItemUpdate,
    current_user: User,
) -> MenuItem:
    canteen = get_canteen_by_id(db, canteen_id)
    _assert_canteen_owner(canteen, current_user)
    item = get_menu_item(db, canteen_id, item_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def delete_menu_item(db, canteen_id, item_id, current_user):
    item = get_menu_item(db, canteen_id, item_id)  # ganti ini
    _assert_canteen_owner(item.canteen, current_user)
    
    item.is_available = False  # soft delete
    db.commit()
