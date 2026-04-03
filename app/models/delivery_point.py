from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class DeliveryPoint(Base):
    __tablename__ = "delivery_points"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    building = Column(String(100), nullable=False)
    floor = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)

    orders = relationship("Order", back_populates="delivery_point")
