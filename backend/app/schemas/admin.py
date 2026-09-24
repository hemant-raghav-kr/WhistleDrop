"""Admin schemas for user and role management."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.moderator import UserRole


class UserAdminRead(BaseModel):
    """Admin view of a registered user/staff account."""
    id: uuid.UUID
    name: Optional[str] = None
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    """Payload to grant or revoke moderator access."""
    role: UserRole = Field(..., description="Target role: must be USER or MODERATOR")

    @field_validator("role")
    @classmethod
    def validate_assignable_role(cls, v: UserRole) -> UserRole:
        if v not in (UserRole.USER, UserRole.MODERATOR):
            raise ValueError("Role can only be changed to USER or MODERATOR.")
        return v
