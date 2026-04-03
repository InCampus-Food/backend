from typing import Optional

from pydantic import BaseModel


class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    category: Optional[str] = None
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    is_available: Optional[bool] = None


class MenuItemResponse(BaseModel):
    id: int
    canteen_id: int
    name: str
    description: Optional[str]
    price: float
    image_url: Optional[str]
    category: Optional[str]
    is_available: bool

    model_config = {"from_attributes": True}
