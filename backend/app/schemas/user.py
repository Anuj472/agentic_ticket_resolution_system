from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole, UserStatus


class UserCreate(BaseModel):
    employee_id: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=2)
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.END_USER
    department: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: UUID
    employee_id: str
    email: str
    full_name: str
    role: UserRole
    department: Optional[str] = None
    status: UserStatus
    is_agent: bool
    created_at: datetime

    model_config = {"from_attributes": True}
