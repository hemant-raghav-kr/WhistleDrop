"""Confidential Report ORM model."""

import enum
from typing import List, Optional
from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ReportStatus(str, enum.Enum):
    """Lifecycle statuses for WhistleDrop reports.

    Permitted state flow:
    SUBMITTED -> UNDER_REVIEW -> RESOLVED
    OR
    SUBMITTED -> UNDER_REVIEW -> DISMISSED
    """
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class ReportCategory(str, enum.Enum):
    """Supported classifications for anonymous reports."""
    SECURITY = "SECURITY"
    HARASSMENT = "HARASSMENT"
    CORRUPTION = "CORRUPTION"
    TECHNICAL = "TECHNICAL"
    OTHER = "OTHER"


class Report(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Anonymously submitted report record.

    Privacy & Security Guarantees:
    - Absolutely no reporter identity fields (name, email, phone, IP, user-agent, session, device fingerprint) are collected or stored.
    - `case_code_hash` stores a one-way HMAC-SHA256 digest of the reporter's secret case code.
      The secret case code consists of 16 Crockford Base32 characters (32^16 = 2^80 combinations).
    - Reporters query using their plaintext case code, which is hashed at query time.
    - Internal database primary keys (UUID) are never revealed across public reporter endpoints.
    """
    __tablename__ = "reports"

    # HMAC-SHA256 digest of case code (64 hex characters)
    case_code_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    evidence_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True,
    )

    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, native_enum=False),
        default=ReportStatus.SUBMITTED,
        nullable=False,
        index=True,
    )

    # Status updates timeline relationship
    status_updates: Mapped[List["StatusUpdate"]] = relationship(
        "StatusUpdate",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="StatusUpdate.created_at.asc()",
    )

    # Evidence files relationship
    evidence_files: Mapped[List["EvidenceFile"]] = relationship(
        "EvidenceFile",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="EvidenceFile.created_at.asc()",
    )

    @property
    def has_evidence(self) -> bool:
        """Helper indicating if report has evidence link or uploaded files."""
        has_url = bool(self.evidence_url and self.evidence_url.strip())
        has_files = bool(self.evidence_files and len(self.evidence_files) > 0)
        return has_url or has_files

    def __repr__(self) -> str:
        return f"<Report id={self.id} status={self.status} category={self.category}>"
