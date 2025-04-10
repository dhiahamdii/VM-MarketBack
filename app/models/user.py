from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime

from . import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Pydantic models for API
class UserBase(BaseModel):
    email: str
    name: str
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: str | None = None
    name: str | None = None
    password: str | None = None
    is_admin: bool | None = None

    model_config = ConfigDict(from_attributes=True)

class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True) 