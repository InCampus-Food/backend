from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import require_role
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.models.canteen import Canteen
from app.schemas.canteen import CanteenResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return query.order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/toggle", response_model=UserResponse)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def change_user_role(
    user_id: int,
    role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    user.role = role
    db.commit()
    db.refresh(user)
    return user


@router.get("/canteens", response_model=List[CanteenResponse])
def list_all_canteens(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    return db.query(Canteen).order_by(Canteen.created_at.desc()).all()


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    from app.models.order import Order, OrderStatus
    from app.models.menu_item import MenuItem

    return {
        "total_users": db.query(User).count(),
        "total_canteens": db.query(Canteen).count(),
        "total_orders": db.query(Order).count(),
        "active_orders": db.query(Order).filter(
            Order.status.in_([OrderStatus.pending, OrderStatus.confirmed, OrderStatus.preparing, OrderStatus.delivering])
        ).count(),
        "total_menu_items": db.query(MenuItem).count(),
        "users_by_role": {
            "customer": db.query(User).filter(User.role == UserRole.customer).count(),
            "canteen": db.query(User).filter(User.role == UserRole.canteen).count(),
            "admin": db.query(User).filter(User.role == UserRole.admin).count(),
        }
    }
