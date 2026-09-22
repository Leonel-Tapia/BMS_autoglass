# /app/schemas/users/user_schema.py | Updated: 2026-05-06 14:10
# Pydantic models for User validation. Fixes Pydantic V2 UserWarning.

from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    role: str

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    location: Optional[str] = None

    phone_1: Optional[str] = None
    phone_2: Optional[str] = None

    is_active: Optional[bool] = True

    position: Optional[str] = None
    salary: Optional[float] = None
    hire_date: Optional[datetime] = None

    class Config:
        # CAMBIO CRÍTICO: Se reemplaza orm_mode por from_attributes para Pydantic V2
        from_attributes = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    location: Optional[str] = None

    phone_1: Optional[str] = None
    phone_2: Optional[str] = None

    is_active: Optional[bool] = None

    position: Optional[str] = None
    salary: Optional[float] = None
    hire_date: Optional[datetime] = None

    password: Optional[str] = None

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True