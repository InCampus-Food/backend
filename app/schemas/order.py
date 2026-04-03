from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.order import OrderStatus
from app.schemas.menu_item import MenuItemResponse


class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int
    notes: Optional[str] = None


class OrderCreate(BaseModel):
    canteen_id: int
    delivery_point_id: int
    items: List[OrderItemCreate]
    notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    quantity: int
    subtotal: float
    notes: Optional[str]
    menu_item: MenuItemResponse

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderResponse(BaseModel):
    id: int
    user_id: int
    canteen_id: int
    delivery_point_id: int
    status: OrderStatus
    total_price: float
    notes: Optional[str]
    ordered_at: datetime
    delivered_at: Optional[datetime]
    items: List[OrderItemResponse]

    model_config = {"from_attributes": True}
