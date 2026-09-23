"""Evidence File ORM model for securely stored anonymous file attachments."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class EvidenceFile(Base, UUIDPrimaryKeyMixin):
    """Metadata record for an uploaded evidence file stored in private object storage.

    Privacy & Security Guarantees:
    - Never stores reporter identity, email, IP address, or device fingerprint.
    - Actual binary file is persisted in private object storage (Supabase Storage);
      never in the relational database.
    - `storage_key` is randomized and unpredictable to prevent enumeration and path traversal.
    - Public case tracking never exposes download links or bucket locations.
    """
    __tablename__ = "evidence_files"

    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        index=True,
        nullable=False,
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    report: Mapped["Report"] = relationship(
        "Report",
        back_populates="evidence_files",
    )

    def __repr__(self) -> str:
        return f"<EvidenceFile id={self.id} report_id={self.report_id} filename='{self.original_filename}'>"
