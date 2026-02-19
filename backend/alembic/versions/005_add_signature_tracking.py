"""Add signature tracking fields to contracts table

Revision ID: 005_add_signature_tracking
Revises: 004_add_premium_subscription
Create Date: 2026-02-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '005_add_signature_tracking'
down_revision = '004_premium_subscription'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add signature tracking fields to contracts table
    op.add_column('contracts', sa.Column('instructor_signed_at', sa.DateTime(), nullable=True))
    op.add_column('contracts', sa.Column('studio_signed_at', sa.DateTime(), nullable=True))

    # Create indexes for better query performance
    op.create_index(op.f('ix_contracts_instructor_signed_at'), 'contracts', ['instructor_signed_at'], unique=False)
    op.create_index(op.f('ix_contracts_studio_signed_at'), 'contracts', ['studio_signed_at'], unique=False)


def downgrade() -> None:
    # Remove indexes
    op.drop_index(op.f('ix_contracts_studio_signed_at'), table_name='contracts')
    op.drop_index(op.f('ix_contracts_instructor_signed_at'), table_name='contracts')

    # Remove columns
    op.drop_column('contracts', 'studio_signed_at')
    op.drop_column('contracts', 'instructor_signed_at')