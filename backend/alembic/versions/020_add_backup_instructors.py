"""Add backup_instructors table.

Revision ID: 020_backup_instructors
Revises: 019_style_matching
Create Date: 2026-03-02
"""
from alembic import op
import sqlalchemy as sa

revision = "020_backup_instructors"
down_revision = "019_style_matching"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backup_instructors",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("studio_id", sa.CHAR(36), sa.ForeignKey("studio_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instructor_id", sa.CHAR(36), sa.ForeignKey("instructor_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nickname", sa.String(50), nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("priority", sa.Integer, default=3),
        sa.Column("last_worked_at", sa.DateTime, nullable=True),
        sa.Column("total_completed", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("studio_id", "instructor_id", name="uq_backup_studio_instructor"),
    )
    op.create_index("ix_backup_instructors_studio_id", "backup_instructors", ["studio_id"])
    op.create_index("ix_backup_instructors_instructor_id", "backup_instructors", ["instructor_id"])


def downgrade() -> None:
    op.drop_index("ix_backup_instructors_instructor_id", table_name="backup_instructors")
    op.drop_index("ix_backup_instructors_studio_id", table_name="backup_instructors")
    op.drop_table("backup_instructors")
