"""Add legal consent and soft-delete fields to users

Adds terms_agreed_at, privacy_agreed_at, deleted_at, deletion_scheduled_at
to the users table.

Revision ID: 012_legal_deletion
Revises: 011_billing_bank_transfer
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012_legal_deletion'
down_revision = '011_billing_bank_transfer'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('terms_agreed_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('privacy_agreed_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('deletion_scheduled_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'deletion_scheduled_at')
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'privacy_agreed_at')
    op.drop_column('users', 'terms_agreed_at')
