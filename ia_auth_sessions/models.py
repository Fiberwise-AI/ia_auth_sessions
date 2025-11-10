"""
Pydantic models for authentication.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Model for user registration."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str


class User(BaseModel):
    """User model (without password)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None


class Session(BaseModel):
    """Session model."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    expires_at: datetime
    created_at: datetime
    metadata: dict = {}
