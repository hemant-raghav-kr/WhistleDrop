"""Pydantic schemas for Evidence Files metadata and access."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class EvidenceFileRead(BaseModel):
    """Sanitized evidence file metadata for moderator viewing.

    Internal storage keys and bucket details are strictly excluded.
    """
    id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size: int = Field(..., description="File size in bytes")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceDownloadResponse(BaseModel):
    """Short-lived signed access payload for authorized moderator downloads."""
    id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size: int
    download_url: str = Field(..., description="Short-lived signed access URL or stream path")
    expires_in: int = Field(300, description="URL validity lifetime in seconds")
