from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

from . import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

# User model with authentication and role management
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    virtual_machines = relationship("VirtualMachine", back_populates="owner")
    payments = relationship("Payment", back_populates="user")

# Pydantic models for API
class UserBase(BaseModel):
    email: EmailStr
    name: str

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: str | None = None
    name: str | None = None
    password: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None

    model_config = ConfigDict(from_attributes=True)

class UserInDB(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True) 