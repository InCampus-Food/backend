from typing import Optional
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    icon: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str]

    model_config = {"from_attributes": True}
