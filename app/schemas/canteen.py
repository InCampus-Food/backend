from datetime import datetime
from typing import Optional, List
from app.schemas.menu_item import MenuItemResponse

from pydantic import BaseModel


class CanteenCreate(BaseModel):
    name: str
    description: Optional[str] = None
    location: Optional[str] = None


class CanteenUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    is_open: Optional[bool] = None


class CanteenResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    location: Optional[str]
    is_open: bool
    image_url: Optional[str]
    created_at: datetime
    menu_items: List[MenuItemResponse] = []
    model_config = {"from_attributes": True}
