"""Add penalty system, verification, deposit, and escrow features

Revision ID: 002_penalty_matching
Revises: 001_initial
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_penalty_matching'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add no-show penalty columns to users
    op.add_column('users', sa.Column('no_show_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default='false'))

    # Add identity verification columns to users
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('identity_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('business_number', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('business_verified', sa.Boolean(), nullable=False, server_default='false'))

    # Add deposit columns to users
    op.add_column('users', sa.Column('deposit_balance', sa.Numeric(10, 2), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('deposit_required', sa.Numeric(10, 2), nullable=False, server_default='50000'))

    # Add escrow status to payments
    op.add_column('payments', sa.Column('escrow_status', sa.String(20), nullable=False, server_default='HELD'))


def downgrade() -> None:
    # Remove escrow status
    op.drop_column('payments', 'escrow_status')

    # Remove deposit columns
    op.drop_column('users', 'deposit_required')
    op.drop_column('users', 'deposit_balance')

    # Remove verification columns
    op.drop_column('users', 'business_verified')
    op.drop_column('users', 'business_number')
    op.drop_column('users', 'identity_verified')
    op.drop_column('users', 'phone_verified')
    op.drop_column('users', 'phone')

    # Remove penalty columns
    op.drop_column('users', 'is_suspended')
    op.drop_column('users', 'no_show_count')
