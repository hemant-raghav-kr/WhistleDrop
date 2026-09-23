"""Status Update audit trail ORM model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin
from app.models.report import ReportStatus


class StatusUpdate(Base, UUIDPrimaryKeyMixin):
    """Historical record / audit entry of every report state transition."""
    __tablename__ = "status_updates"

    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, native_enum=False),
        nullable=False,
    )

    update_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    report: Mapped["Report"] = relationship(
        "Report",
        back_populates="status_updates",
    )

    def __repr__(self) -> str:
        return f"<StatusUpdate report_id={self.report_id} status={self.status}>"
