"""Initial schema for WhistleDrop foundation.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-23 20:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. moderators table
    op.create_table(
        "moderators",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_moderators_id"), "moderators", ["id"], unique=False)
    op.create_index(op.f("ix_moderators_email"), "moderators", ["email"], unique=True)
    op.create_index(op.f("ix_moderators_username"), "moderators", ["username"], unique=True)

    # 2. reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_code_hash", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence_url", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_id"), "reports", ["id"], unique=False)
    op.create_index(op.f("ix_reports_case_code_hash"), "reports", ["case_code_hash"], unique=True)
    op.create_index(op.f("ix_reports_category"), "reports", ["category"], unique=False)
    op.create_index(op.f("ix_reports_status"), "reports", ["status"], unique=False)

    # 3. status_updates table
    op.create_table(
        "status_updates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("update_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_status_updates_id"), "status_updates", ["id"], unique=False)
    op.create_index(op.f("ix_status_updates_report_id"), "status_updates", ["report_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_status_updates_report_id"), table_name="status_updates")
    op.drop_index(op.f("ix_status_updates_id"), table_name="status_updates")
    op.drop_table("status_updates")

    op.drop_index(op.f("ix_reports_status"), table_name="reports")
    op.drop_index(op.f("ix_reports_category"), table_name="reports")
    op.drop_index(op.f("ix_reports_case_code_hash"), table_name="reports")
    op.drop_index(op.f("ix_reports_id"), table_name="reports")
    op.drop_table("reports")

    op.drop_index(op.f("ix_moderators_username"), table_name="moderators")
    op.drop_index(op.f("ix_moderators_email"), table_name="moderators")
    op.drop_index(op.f("ix_moderators_id"), table_name="moderators")
    op.drop_table("moderators")
