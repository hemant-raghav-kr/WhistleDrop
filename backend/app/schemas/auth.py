"""Authentication and registration schemas."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.moderator import UserRole


class LoginRequest(BaseModel):
    """User/Moderator/Admin login credentials."""
    username_or_email: str = Field(..., description="Registered username or email")
    password: str = Field(..., min_length=8, description="Account password")


class RegisterRequest(BaseModel):
    """New user registration payload. Always creates role = USER."""
    name: str = Field(..., min_length=2, max_length=100, description="Full name or display name")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (at least 8 characters)")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Must match password")

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 2:
            raise ValueError("Name must contain at least 2 characters.")
        return trimmed

    @model_validator(mode="after")
    def verify_passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class UserRead(BaseModel):
    """Public read representation of an authenticated user."""
    id: uuid.UUID
    name: Optional[str] = None
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT response structure."""
    access_token: str
    token_type: str = "bearer"
    role: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None


class TokenPayload(BaseModel):
    """Decoded JWT payload structure."""
    sub: Optional[str] = None
    exp: Optional[int] = None
