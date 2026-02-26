"""Add payment_cancellations, webhook_events tables and Payment cancel columns

- payment_cancellations table (new)
- webhook_events table (new)
- payments.cancelled_amount NUMERIC(10,2) default 0
- payments.balance_amount NUMERIC(10,2) nullable

Revision ID: 014_payment_cancel_webhook
Revises: 013_photo_notif_device
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '014_payment_cancel_webhook'
down_revision = '013_photo_notif_device'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Payment cancellation columns
    op.add_column('payments', sa.Column('cancelled_amount', sa.Numeric(10, 2), server_default='0'))
    op.add_column('payments', sa.Column('balance_amount', sa.Numeric(10, 2), nullable=True))

    # Payment cancellations table
    op.create_table(
        'payment_cancellations',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('payment_id', sa.CHAR(36), sa.ForeignKey('payments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cancel_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('cancel_reason', sa.String(200), nullable=False),
        sa.Column('cancel_status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('idempotency_key', sa.String(100), unique=True, nullable=True),
        sa.Column('tax_free_amount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('pg_cancel_response', sa.JSON(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('requested_by_user_id', sa.CHAR(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('transaction_key', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_payment_cancellations_payment_id', 'payment_cancellations', ['payment_id'])
    op.create_index('ix_payment_cancellations_idempotency_key', 'payment_cancellations', ['idempotency_key'])

    # Webhook events table
    op.create_table(
        'webhook_events',
        sa.Column('transmission_id', sa.String(100), primary_key=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('payment_key', sa.String(200), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_webhook_events_payment_key', 'webhook_events', ['payment_key'])


def downgrade() -> None:
    op.drop_index('ix_webhook_events_payment_key', table_name='webhook_events')
    op.drop_table('webhook_events')
    op.drop_index('ix_payment_cancellations_idempotency_key', table_name='payment_cancellations')
    op.drop_index('ix_payment_cancellations_payment_id', table_name='payment_cancellations')
    op.drop_table('payment_cancellations')
    op.drop_column('payments', 'balance_amount')
    op.drop_column('payments', 'cancelled_amount')
