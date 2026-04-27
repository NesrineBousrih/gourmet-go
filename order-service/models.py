from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from database import Base

class Order(Base):
    __tablename__ = "orders"

    order_id  = Column(String, primary_key=True, index=True)
    status    = Column(String, nullable=False, default="APPROVAL_PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())