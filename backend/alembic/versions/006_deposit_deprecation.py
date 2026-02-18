"""Deprecate deposit system (v3.0)

Revision ID: 006_deposit_deprecation
Revises: 005_add_signature_tracking
Create Date: 2026-02-18

This migration marks deposit-related columns as deprecated.
These columns are retained for historical data but are no longer used.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_deposit_deprecation'
down_revision = '005_add_signature_tracking'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Mark deposit columns as deprecated - no longer used in v3.0."""
    # Add comments to document deprecation status (execute separately)
    op.execute("COMMENT ON COLUMN users.deposit_balance IS 'DEPRECATED v3.0 - No deposit system'")
    op.execute("COMMENT ON COLUMN users.deposit_required IS 'DEPRECATED v3.0 - No deposit system'")
    op.execute("COMMENT ON COLUMN users.deposit_first_paid_at IS 'DEPRECATED v3.0 - No deposit system'")
    op.execute("COMMENT ON COLUMN users.is_early_bird IS 'DEPRECATED v3.0 - No deposit system'")

    # Set all deposit requirements to 0 for active users
    op.execute("UPDATE users SET deposit_required = 0 WHERE deposit_required > 0")

    # Note: We keep the columns and data for historical purposes.
    # Full cleanup can be done in a future migration after data archival.


def downgrade() -> None:
    """Restore deposit system (if needed to rollback)."""
    # Remove deprecation comments (execute separately)
    op.execute("COMMENT ON COLUMN users.deposit_balance IS NULL")
    op.execute("COMMENT ON COLUMN users.deposit_required IS NULL")
    op.execute("COMMENT ON COLUMN users.deposit_first_paid_at IS NULL")
    op.execute("COMMENT ON COLUMN users.is_early_bird IS NULL")

    # Restore default deposit requirements
    op.execute("UPDATE users SET deposit_required = 50000 WHERE deposit_required = 0 AND membership_tier != 'premium'")