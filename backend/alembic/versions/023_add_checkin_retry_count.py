"""Add retry_count to checkin_records for check-in retry support.

Revision ID: 023_add_checkin_retry_count
Revises: 8afa6f26e1fa
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa

revision = "023_add_checkin_retry_count"
down_revision = "8afa6f26e1fa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "checkin_records",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("checkin_records", "retry_count")
