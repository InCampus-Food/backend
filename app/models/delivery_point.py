from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class DeliveryPoint(Base):
    __tablename__ = "delivery_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    building = Column(String(100), nullable=False)
    floor = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_default = Column(Boolean, default=False)

    user = relationship("User", back_populates="delivery_points")
    orders = relationship("Order", back_populates="delivery_point")
