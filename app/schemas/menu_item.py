from typing import Optional
from pydantic import BaseModel
from app.schemas.category import CategoryResponse


class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_available: Optional[bool] = None


class MenuItemResponse(BaseModel):
    id: int
    canteen_id: int
    name: str
    description: Optional[str]
    price: float
    image_url: Optional[str]
    is_available: bool
    category_id: Optional[int]
    category_rel: Optional[CategoryResponse] = None

    model_config = {"from_attributes": True}
