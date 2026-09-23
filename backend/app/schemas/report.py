"""Pydantic schemas for confidential reports with strict validation.

Privacy Guarantees:
- ReportCreate takes NO reporter identity attributes (zero-knowledge).
- Category validated against supported categories with case-insensitive normalization.
- Description and evidence_url strictly validated.
- ReportPublicCreated only returns the generated plaintext case code, category, status, and created_at.
- ReportPublicLookup conceals internal database UUIDs, hashes, and moderator details.
- ReportModeratorRead is reserved for authenticated moderator views.
"""

import re
import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.report import ReportCategory, ReportStatus
from app.schemas.evidence import EvidenceFileRead
from app.schemas.status_update import PublicStatusUpdateRead, StatusUpdateRead

# URL validation pattern requiring http:// or https:// prefix
HTTP_URL_REGEX = re.compile(
    r"^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+$",
    re.IGNORECASE,
)


class ReportBase(BaseModel):
    category: str = Field(
        ...,
        description="Report classification: SECURITY, HARASSMENT, CORRUPTION, TECHNICAL, or OTHER",
        examples=["TECHNICAL"],
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Detailed factual description of the incident (10-10,000 characters)",
        examples=["Observed unauthorized modification of database configurations during maintenance window."],
    )
    evidence_url: Optional[str] = Field(
        None,
        max_length=1024,
        description="Optional public reference or evidence link (must be http:// or https://)",
        examples=["https://example.com/evidence/log.txt"],
    )

    @field_validator("category", mode="before")
    @classmethod
    def validate_and_normalize_category(cls, v: Any) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Category is required and must be a non-empty string.")
        normalized = v.strip().upper()
        valid_categories = {c.value for c in ReportCategory}
        if normalized not in valid_categories:
            valid_list = ", ".join(sorted(valid_categories))
            raise ValueError(
                f"Invalid category '{v}'. Supported categories are: [{valid_list}]"
            )
        return normalized

    @field_validator("description")
    @classmethod
    def validate_description_content(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 10:
            raise ValueError("Description must contain at least 10 non-whitespace characters.")
        return trimmed

    @field_validator("evidence_url")
    @classmethod
    def validate_evidence_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            return None
        if not HTTP_URL_REGEX.match(trimmed):
            raise ValueError("Evidence URL must be a valid HTTP or HTTPS URL (e.g. https://example.com).")
        return trimmed


class ReportCreate(ReportBase):
    """Anonymous report submission payload. Absolutely no reporter identity fields."""
    pass


class ReportPublicCreated(BaseModel):
    """Response returned once upon successful report creation.

    Note:
    - Internal database primary keys (UUID) are NEVER revealed to the reporter.
    - The `case_code` is displayed once for the reporter to store securely.
    """
    case_code: str = Field(..., description="Cryptographically secure tracking code. Store safely!")
    category: str
    status: ReportStatus
    created_at: datetime
    has_evidence: bool = Field(default=False, description="Flag indicating if evidence was attached")

    model_config = ConfigDict(from_attributes=True)


class ReportPublicLookup(BaseModel):
    """Public read model returned when tracking a case via its case code.

    Guarantees:
    - Internal database ID is omitted.
    - Case code hash is omitted.
    - Moderator identity is omitted.
    - Public status timeline updates are included.
    """
    category: str
    status: ReportStatus
    submitted_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("created_at", "submitted_at"),
        description="Timestamp when report was submitted",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when report was submitted (alias for submitted_at)",
    )
    updated_at: datetime = Field(..., description="Timestamp of latest modification")
    updates: List[PublicStatusUpdateRead] = Field(
        default_factory=list,
        validation_alias=AliasChoices("status_updates", "updates"),
        description="Public lifecycle updates timeline",
    )
    status_updates: List[PublicStatusUpdateRead] = Field(
        default_factory=list,
        description="Public updates timeline (alias for updates)",
    )
    has_evidence: bool = Field(
        default=False,
        description="Indicates whether external link or file evidence was attached",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def synchronize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "status_updates" in data and "updates" not in data:
                data["updates"] = data["status_updates"]
            if "created_at" in data and "submitted_at" not in data:
                data["submitted_at"] = data["created_at"]
        return data


class ReportModeratorRead(BaseModel):
    """Comprehensive report model accessible only to authenticated moderators."""
    id: uuid.UUID
    category: str
    description: str
    evidence_url: Optional[str] = None
    status: ReportStatus
    created_at: datetime
    updated_at: datetime
    status_updates: List[StatusUpdateRead] = []
    updates: List[PublicStatusUpdateRead] = Field(
        default_factory=list,
        validation_alias=AliasChoices("status_updates", "updates"),
    )
    evidence_files: List[EvidenceFileRead] = Field(
        default_factory=list,
        description="List of securely stored evidence file attachments",
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ReportStatusTransitionRequest(BaseModel):
    """Payload submitted by moderators to transition a report status."""
    status: ReportStatus = Field(
        ...,
        description="Target status (SUBMITTED -> UNDER_REVIEW -> RESOLVED or DISMISSED)",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Public explanation or resolution note visible on the report tracking timeline",
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Status message cannot be empty or whitespace only.")
        return trimmed
