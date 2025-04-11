from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from ..models.user import UserRole

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class User(UserBase):
    id: int
    role: UserRole = UserRole.USER
    is_active: bool = True

    model_config = {
        "from_attributes": True
    } 