from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    """
    Base user schema detailing properties shared by registration and profile read.
    """
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Unique email address")
    role: str = Field(default="operator", description="System user authorization role ('admin' or 'operator')")

class UserCreate(UserBase):
    """
    Schema for creating a new user, requiring password validation.
    """
    password: str = Field(..., min_length=6, max_length=100, description="Clear-text password")

class UserResponse(UserBase):
    """
    Schema representing user account information returned in API responses.
    """
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """
    Schema validation rules for logging in with username and password.
    """
    username: str = Field(..., description="User's username")
    password: str = Field(..., description="User's cleartext password")

class TokenResponse(BaseModel):
    """
    JSON response containing the JWT access token.
    """
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str

class TokenData(BaseModel):
    """
    Decoded payload structure mapped from JWT claim keys.
    """
    username: Optional[str] = None
    role: Optional[str] = None
