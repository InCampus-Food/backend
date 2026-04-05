from typing import Optional
from pydantic import BaseModel


class DeliveryPointCreate(BaseModel):
    name: str
    building: str
    floor: Optional[str] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False


class DeliveryPointUpdate(BaseModel):
    name: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: Optional[bool] = None


class DeliveryPointResponse(BaseModel):
    id: int
    user_id: int
    name: str
    building: str
    floor: Optional[str]
    notes: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    is_default: bool

    model_config = {"from_attributes": True}
