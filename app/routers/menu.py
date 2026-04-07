from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.menu_item import MenuItemCreate, MenuItemUpdate, MenuItemResponse
from app.services import menu_service

router = APIRouter(prefix="/canteens/{canteen_id}/menu", tags=["Menu"])


@router.get("", response_model=List[MenuItemResponse])
def list_menu(
    canteen_id: int,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    include_unavailable: Optional[bool] = None
):
    return menu_service.list_menu_items(db, canteen_id, category, include_unavailable)


@router.post("", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
def create_menu_item(
    canteen_id: int,
    payload: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.canteen, UserRole.admin)),
):
    return menu_service.create_menu_item(db, canteen_id, payload, current_user)


@router.patch("/{item_id}", response_model=MenuItemResponse)
def update_menu_item(
    canteen_id: int,
    item_id: int,
    payload: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.canteen, UserRole.admin)),
):
    return menu_service.update_menu_item(db, canteen_id, item_id, payload, current_user)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    canteen_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.canteen, UserRole.admin)),
):
    menu_service.delete_menu_item(db, canteen_id, item_id, current_user)
