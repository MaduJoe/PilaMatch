"""Add billing key and bank transfer fields to subscriptions

Adds toss_customer_key, card_last_four, card_company to subscriptions table.
Adds payment_type, bank_transfer_confirmed_by, bank_transfer_confirmed_at
to subscription_payments table.

Revision ID: 011_billing_bank_transfer
Revises: 010_contract_content_hash
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011_billing_bank_transfer'
down_revision = '010_contract_content_hash'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Subscriptions: billing key fields
    op.add_column('subscriptions', sa.Column('toss_customer_key', sa.String(200), nullable=True))
    op.add_column('subscriptions', sa.Column('card_last_four', sa.String(4), nullable=True))
    op.add_column('subscriptions', sa.Column('card_company', sa.String(50), nullable=True))

    # Subscription payments: bank transfer fields
    op.add_column('subscription_payments', sa.Column('payment_type', sa.String(20), server_default='initial', nullable=True))
    op.add_column('subscription_payments', sa.Column('bank_transfer_confirmed_by', sa.String(36), nullable=True))
    op.add_column('subscription_payments', sa.Column('bank_transfer_confirmed_at', sa.DateTime(), nullable=True))

    op.create_foreign_key(
        'fk_subscription_payments_confirmed_by',
        'subscription_payments', 'users',
        ['bank_transfer_confirmed_by'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_subscription_payments_confirmed_by', 'subscription_payments', type_='foreignkey')
    op.drop_column('subscription_payments', 'bank_transfer_confirmed_at')
    op.drop_column('subscription_payments', 'bank_transfer_confirmed_by')
    op.drop_column('subscription_payments', 'payment_type')
    op.drop_column('subscriptions', 'card_company')
    op.drop_column('subscriptions', 'card_last_four')
    op.drop_column('subscriptions', 'toss_customer_key')
