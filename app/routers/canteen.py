from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.canteen import CanteenCreate, CanteenUpdate, CanteenResponse
from app.services import canteen_service

router = APIRouter(prefix="/canteens", tags=["Canteens"])


@router.get("", response_model=List[CanteenResponse])
def list_canteens(db: Session = Depends(get_db)):
    return canteen_service.get_all_open_canteens(db)


@router.get("/{canteen_id}", response_model=CanteenResponse)
def get_canteen(canteen_id: int, db: Session = Depends(get_db)):
    return canteen_service.get_canteen_by_id(db, canteen_id)


@router.post("", response_model=CanteenResponse, status_code=status.HTTP_201_CREATED)
def create_canteen(
    payload: CanteenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.canteen, UserRole.admin)),
):
    return canteen_service.create_canteen(db, payload, current_user)


@router.patch("/{canteen_id}", response_model=CanteenResponse)
def update_canteen(
    canteen_id: int,
    payload: CanteenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.canteen, UserRole.admin)),
):
    return canteen_service.update_canteen(db, canteen_id, payload, current_user)


@router.patch("/{canteen_id}/toggle", response_model=CanteenResponse)
def toggle_canteen(
    canteen_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.canteen, UserRole.admin)),
):
    return canteen_service.toggle_canteen_status(db, canteen_id, current_user)