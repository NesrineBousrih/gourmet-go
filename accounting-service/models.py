from sqlalchemy import Column, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class Payment(Base):
    __tablename__ = "payments"

    order_id   = Column(String, primary_key=True, index=True)
    amount     = Column(Float, nullable=False)
    authorized = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())