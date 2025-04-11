from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from . import Base

class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    stripe_payment_id = Column(String, unique=True, index=True)
    amount = Column(Float)
    status = Column(String, default=PaymentStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Add foreign key to User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="payments")

# Pydantic models
class PaymentBase(BaseModel):
    stripe_payment_id: str
    amount: float
    status: PaymentStatus

    model_config = ConfigDict(from_attributes=True)

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    status: PaymentStatus

    model_config = ConfigDict(from_attributes=True)

class PaymentInDB(PaymentBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True) 