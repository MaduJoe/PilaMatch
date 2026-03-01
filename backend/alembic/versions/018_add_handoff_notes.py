"""Add handoff_notes table.

Stores per-job-post handoff notes so studios can share class context
(topic, sequence, atmosphere, member/equipment notes) with substitute
instructors.

Revision ID: 018_handoff_notes
Revises: 017_event_logs
Create Date: 2026-03-02
"""

from alembic import op
import sqlalchemy as sa

revision = "018_handoff_notes"
down_revision = "017_event_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "handoff_notes",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column(
            "job_post_id",
            sa.CHAR(36),
            sa.ForeignKey("job_posts.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "author_user_id",
            sa.CHAR(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("class_topic", sa.String(200), nullable=True),
        sa.Column("class_sequence_info", sa.Text, nullable=True),
        sa.Column("atmosphere_preference", sa.String(50), nullable=True),
        sa.Column("additional_notes", sa.Text, nullable=True),
        sa.Column("member_notes", sa.Text, nullable=True),
        sa.Column("equipment_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index(
        "ix_handoff_notes_job_post_id", "handoff_notes", ["job_post_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_handoff_notes_job_post_id", table_name="handoff_notes")
    op.drop_table("handoff_notes")
