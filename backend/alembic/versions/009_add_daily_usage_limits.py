"""Add daily usage limits tracking for premium features

Revision ID: 009_daily_limits
Revises: 008_add_application_templates
Create Date: 2026-02-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '009_daily_limits'
down_revision = '008_add_application_templates'
branch_labels = None
depends_on = None


def upgrade():
    # Create daily_usage_limits table for tracking daily usage
    op.create_table('daily_usage_limits',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('usage_date', sa.Date(), nullable=False),
        sa.Column('usage_type', sa.String(50), nullable=False),  # 'application', 'profile_view'
        sa.Column('count', sa.Integer(), default=0, nullable=False),
        sa.Column('max_limit', sa.Integer(), nullable=True),  # NULL for unlimited (premium)
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'usage_date', 'usage_type', name='uq_user_date_type')
    )

    # Add index for faster lookups
    op.create_index('idx_daily_usage_user_date', 'daily_usage_limits', ['user_id', 'usage_date'])

    # Add premium badge field to users table (allow nulls initially)
    op.add_column('users', sa.Column('has_premium_badge', sa.Boolean(), nullable=True))

    # Set default value for existing records
    op.execute("UPDATE users SET has_premium_badge = false WHERE has_premium_badge IS NULL")

    # Update existing premium users to have badge
    op.execute("UPDATE users SET has_premium_badge = true WHERE membership_tier = 'premium'")

    # Now make the column NOT NULL
    op.alter_column('users', 'has_premium_badge', nullable=False)

    # Add last_viewed_profiles JSON column for tracking viewed instructor IDs
    op.add_column('users', sa.Column('last_viewed_profiles', sa.JSON(), nullable=True))

    # Add daily usage stats columns for quick reference (nullable first)
    op.add_column('users', sa.Column('daily_applications_today', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('daily_views_today', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('last_usage_reset_date', sa.Date(), nullable=True))

    # Set default values for existing records
    op.execute("UPDATE users SET daily_applications_today = 0 WHERE daily_applications_today IS NULL")
    op.execute("UPDATE users SET daily_views_today = 0 WHERE daily_views_today IS NULL")

    # Now make the counter columns NOT NULL
    op.alter_column('users', 'daily_applications_today', nullable=False)
    op.alter_column('users', 'daily_views_today', nullable=False)


def downgrade():
    # Remove columns from users table
    op.drop_column('users', 'last_usage_reset_date')
    op.drop_column('users', 'daily_views_today')
    op.drop_column('users', 'daily_applications_today')
    op.drop_column('users', 'last_viewed_profiles')
    op.drop_column('users', 'has_premium_badge')

    # Drop index and table
    op.drop_index('idx_daily_usage_user_date', 'daily_usage_limits')
    op.drop_table('daily_usage_limits')