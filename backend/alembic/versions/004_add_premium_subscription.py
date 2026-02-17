"""Add premium subscription system

Revision ID: 004_premium_subscription
Revises: 003_prdv2_updates
Create Date: 2026-02-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_premium_subscription'
down_revision = '003_prdv2_updates'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('tier', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('next_billing_date', sa.DateTime(), nullable=True),
        sa.Column('billing_cycle_day', sa.Integer(), nullable=True),
        sa.Column('monthly_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('auto_renew', sa.Boolean(), nullable=False),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('toss_billing_key', sa.String(length=200), nullable=True),
        sa.Column('payment_method_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_subscription_user', 'subscriptions', ['user_id'], unique=False)
    op.create_index('idx_subscription_status', 'subscriptions', ['status'], unique=False)
    op.create_index('idx_subscription_next_billing', 'subscriptions', ['next_billing_date'], unique=False)

    # Create subscription_payments table
    op.create_table('subscription_payments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('subscription_id', sa.String(length=36), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('payment_date', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=False),
        sa.Column('order_id', sa.String(length=200), nullable=False),
        sa.Column('toss_payment_key', sa.String(length=200), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('last_retry_at', sa.DateTime(), nullable=True),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id'),
        sa.UniqueConstraint('toss_payment_key')
    )
    op.create_index('idx_payment_subscription', 'subscription_payments', ['subscription_id'], unique=False)
    op.create_index('idx_payment_status', 'subscription_payments', ['status'], unique=False)
    op.create_index('idx_payment_order', 'subscription_payments', ['order_id'], unique=False)

    # Create subscription_history table
    op.create_table('subscription_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('old_tier', sa.String(length=20), nullable=True),
        sa.Column('new_tier', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.String(length=50), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('performed_by', sa.String(length=36), nullable=True),
        sa.Column('payment_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['payment_id'], ['subscription_payments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_history_user', 'subscription_history', ['user_id'], unique=False)
    op.create_index('idx_history_created', 'subscription_history', ['created_at'], unique=False)

    # Add column to users table
    op.add_column('users', sa.Column('membership_tier', sa.String(length=20), nullable=False, server_default='free'))

    # Remove server default after adding column (to avoid issues with existing rows)
    op.alter_column('users', 'membership_tier', server_default=None)


def downgrade() -> None:
    # Drop column from users table
    op.drop_column('users', 'membership_tier')

    # Drop indexes
    op.drop_index('idx_history_created', table_name='subscription_history')
    op.drop_index('idx_history_user', table_name='subscription_history')
    op.drop_index('idx_payment_order', table_name='subscription_payments')
    op.drop_index('idx_payment_status', table_name='subscription_payments')
    op.drop_index('idx_payment_subscription', table_name='subscription_payments')
    op.drop_index('idx_subscription_next_billing', table_name='subscriptions')
    op.drop_index('idx_subscription_status', table_name='subscriptions')
    op.drop_index('idx_subscription_user', table_name='subscriptions')

    # Drop tables
    op.drop_table('subscription_history')
    op.drop_table('subscription_payments')
    op.drop_table('subscriptions')