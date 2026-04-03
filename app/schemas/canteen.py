from datetime import datetime
from typing import Optional

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
    created_at: datetime

    model_config = {"from_attributes": True}
