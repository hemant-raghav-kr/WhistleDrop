"""Moderator schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ModeratorBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class ModeratorCreate(ModeratorBase):
    password: str = Field(..., min_length=8)


class ModeratorRead(ModeratorBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
