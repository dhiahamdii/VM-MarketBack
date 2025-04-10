from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BaseResponse(BaseModel):
    message: str
    status: int = 200

class ErrorResponse(BaseResponse):
    detail: str
    status: int = 400

class TimestampedModel(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None 