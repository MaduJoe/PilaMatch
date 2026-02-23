"""Add content_hash column to contracts table for non-repudiation

SHA-256 hash of contract content captured at signing time.
Allows verification that contract terms were not altered after signing.

Revision ID: 010_contract_content_hash
Revises: 009_daily_limits
Create Date: 2026-02-23
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010_contract_content_hash'
down_revision = '009_daily_limits'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'contracts',
        sa.Column('content_hash', sa.String(64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('contracts', 'content_hash')
