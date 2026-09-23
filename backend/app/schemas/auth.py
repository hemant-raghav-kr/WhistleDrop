"""Authentication schemas for moderators."""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Moderator login credentials."""
    username_or_email: str = Field(..., description="Moderator username or registered email")
    password: str = Field(..., min_length=8, description="Moderator password")


class Token(BaseModel):
    """JWT response structure."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload structure."""
    sub: Optional[str] = None
    exp: Optional[int] = None
