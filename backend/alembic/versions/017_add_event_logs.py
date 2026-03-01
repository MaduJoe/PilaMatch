"""Add event_logs table for unified cross-domain audit trails

- Create event_logs table with event_type, actor_user_id, target_type/id, JSON data
- Index on event_type, actor_user_id, composite (target_type, target_id)
- IF NOT EXISTS guard: table may already exist from raw SQL hotfix

Revision ID: 017_event_logs
Revises: 016_trust_tier
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa

revision = '017_event_logs'
down_revision = '016_trust_tier'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Guard: table may already exist from a raw SQL hotfix
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'event_logs')"
    ))
    if result.scalar():
        return  # Table already exists from hotfix

    # -- event_logs ---------------------------------------------------------------
    op.create_table(
        'event_logs',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('event_type', sa.String(50), nullable=False, index=True),
        sa.Column('actor_user_id', sa.CHAR(36), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('target_type', sa.String(50), nullable=True),
        sa.Column('target_id', sa.String(36), nullable=True),
        sa.Column('data', sa.JSON(), server_default='{}'),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Composite index for efficient event queries by target entity
    op.create_index(
        'ix_event_logs_target_type_target_id',
        'event_logs',
        ['target_type', 'target_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_event_logs_target_type_target_id', table_name='event_logs')
    op.drop_table('event_logs')
