"""Add photo_url to profiles, create notifications and device_tokens tables

- instructor_profiles.photo_url VARCHAR(500) nullable
- studio_profiles.photo_url VARCHAR(500) nullable
- notifications table (new)
- device_tokens table (new)

Revision ID: 013_photo_notif_device
Revises: 012_legal_deletion
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '013_photo_notif_device'
down_revision = '012_legal_deletion'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Profile photo fields
    op.add_column('instructor_profiles', sa.Column('photo_url', sa.String(500), nullable=True))
    op.add_column('studio_profiles', sa.Column('photo_url', sa.String(500), nullable=True))

    # Notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('user_id', sa.CHAR(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.String(30), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('data_json', sa.JSON(), nullable=True),
        sa.Column('is_read', sa.Boolean(), default=False, nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])

    # Device tokens table
    op.create_table(
        'device_tokens',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('user_id', sa.CHAR(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token', sa.String(500), nullable=False, unique=True),
        sa.Column('platform', sa.String(20), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_device_tokens_user_id', 'device_tokens', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_device_tokens_user_id', table_name='device_tokens')
    op.drop_table('device_tokens')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
    op.drop_column('studio_profiles', 'photo_url')
    op.drop_column('instructor_profiles', 'photo_url')
