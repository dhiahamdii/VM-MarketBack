from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from enum import Enum as PyEnum
from datetime import datetime

from . import Base

class VMStatus(str, PyEnum):
    AVAILABLE = "available"
    SOLD = "sold"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"

class VirtualMachine(Base):
    __tablename__ = "virtual_machines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    specifications = Column(JSON)  # Store CPU, RAM, Storage as JSON
    price = Column(Float)
    image_type = Column(String)
    status = Column(String, default=VMStatus.AVAILABLE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    tags = Column(JSON)  # Store tags/categories as JSON array

# Pydantic models for API
class VMSpecifications(BaseModel):
    cpu_cores: int
    ram_gb: int
    storage_gb: int
    os_type: str
    
    model_config = ConfigDict(from_attributes=True)

class VMBase(BaseModel):
    name: str
    description: str
    specifications: VMSpecifications
    price: float
    image_type: str
    tags: List[str]
    
    model_config = ConfigDict(from_attributes=True)

class VMCreate(VMBase):
    pass

class VMUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[VMSpecifications] = None
    price: Optional[float] = None
    image_type: Optional[str] = None
    status: Optional[VMStatus] = None
    tags: Optional[List[str]] = None
    
    model_config = ConfigDict(from_attributes=True)

class VMInDB(VMBase):
    id: int
    status: VMStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True) 