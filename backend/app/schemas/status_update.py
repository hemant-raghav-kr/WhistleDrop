"""Pydantic schemas for Report Status Updates."""

import uuid
from datetime import datetime
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.report import ReportStatus


class StatusUpdateBase(BaseModel):
    status: ReportStatus
    update_message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Public explanation or note describing this status update",
    )


class StatusUpdateCreate(StatusUpdateBase):
    pass


class PublicStatusUpdateRead(BaseModel):
    """Sanitized status update item displayed on public case tracking timeline."""
    status: ReportStatus
    message: str = Field(
        ...,
        validation_alias=AliasChoices("update_message", "message"),
        description="Public message describing this update",
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class StatusUpdateRead(StatusUpdateBase):
    """Full status update schema for moderator view."""
    id: uuid.UUID
    message: str = Field(
        ...,
        validation_alias=AliasChoices("update_message", "message"),
        description="Public message describing this update",
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
