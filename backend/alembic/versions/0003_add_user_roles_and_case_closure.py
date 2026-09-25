"""Add user roles and permanent case closure fields.

Revision ID: 0003_add_user_roles_and_case_closure
Revises: 0002_add_evidence_files
Create Date: 2026-09-23 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_add_user_roles_and_case_closure"
down_revision: Union[str, None] = "0002_add_evidence_files"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add name and role to moderators table
    op.add_column("moderators", sa.Column("name", sa.String(length=255), nullable=True))
    op.add_column("moderators", sa.Column("role", sa.String(length=20), nullable=False, server_default=sa.text("'USER'")))
    op.create_index(op.f("ix_moderators_role"), "moderators", ["role"], unique=False)

    # Add is_closed and closed_at to reports table
    op.add_column("reports", sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("reports", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_reports_is_closed"), "reports", ["is_closed"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reports_is_closed"), table_name="reports")
    op.drop_column("reports", "closed_at")
    op.drop_column("reports", "is_closed")

    op.drop_index(op.f("ix_moderators_role"), table_name="moderators")
    op.drop_column("moderators", "role")
    op.drop_column("moderators", "name")
