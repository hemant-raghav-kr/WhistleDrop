"""Add evidence_files table for secure anonymous attachments.

Revision ID: 0002_add_evidence_files
Revises: 0001_initial_schema
Create Date: 2026-09-23 21:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_add_evidence_files"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evidence_files",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidence_files_id"), "evidence_files", ["id"], unique=False)
    op.create_index(op.f("ix_evidence_files_report_id"), "evidence_files", ["report_id"], unique=False)
    op.create_index(op.f("ix_evidence_files_storage_key"), "evidence_files", ["storage_key"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_evidence_files_storage_key"), table_name="evidence_files")
    op.drop_index(op.f("ix_evidence_files_report_id"), table_name="evidence_files")
    op.drop_index(op.f("ix_evidence_files_id"), table_name="evidence_files")
    op.drop_table("evidence_files")
