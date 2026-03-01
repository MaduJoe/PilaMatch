"""Add style matching columns.

Revision ID: 019_style_matching
Revises: 018_handoff_notes
Create Date: 2026-03-02
"""
from alembic import op
import sqlalchemy as sa

revision = "019_style_matching"
down_revision = "018_handoff_notes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("instructor_profiles", sa.Column("teaching_style", sa.JSON, nullable=True))
    op.add_column("job_posts", sa.Column("preferred_style", sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("job_posts", "preferred_style")
    op.drop_column("instructor_profiles", "teaching_style")
