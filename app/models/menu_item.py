from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    canteen_id = Column(Integer, ForeignKey("canteens.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    image_url = Column(String(500), nullable=True)
    is_available = Column(Boolean, default=True)

    canteen = relationship("Canteen", back_populates="menu_items")
    category_rel = relationship("Category", back_populates="menu_items")
    order_items = relationship("OrderItem", back_populates="menu_item")
