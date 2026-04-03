from typing import Optional
from pydantic import BaseModel


class DeliveryPointCreate(BaseModel):
    name: str
    building: str
    floor: Optional[str] = None
    notes: Optional[str] = None


class DeliveryPointResponse(BaseModel):
    id: int
    name: str
    building: str
    floor: Optional[str]
    notes: Optional[str]

    model_config = {"from_attributes": True}
