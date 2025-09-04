"""
Pydantic schemas for User API
"""
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from app.models.user import UserRole, Department


class UserCreate(BaseModel):
    full_name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Unique email")
    role: UserRole = Field(..., description="Role")
    department: Department = Field(..., description="Department")


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    department: Department
    last_contact_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    skip: int
    limit: int

