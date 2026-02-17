"""PRDv2.0.0 updates for trust, completion, and churn tracking

Revision ID: 003_prdv2_updates
Revises: 002_penalty_matching
Create Date: 2026-02-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from app.models.base import GUID
from datetime import datetime, timezone

# revision identifiers
revision = '003_prdv2_updates'
down_revision = '002_penalty_matching'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update users table with v2.0 fields
    op.add_column('users', sa.Column('deposit_first_paid_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('is_early_bird', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('last_active_at', sa.DateTime(),
                                      nullable=False, server_default=sa.func.now()))
    op.add_column('users', sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('trust_score', sa.Integer(), nullable=False, server_default='0'))

    # Update default deposit to 30000 (early bird)
    op.execute("UPDATE users SET deposit_required = 30000 WHERE deposit_required = 50000")

    # Update contracts table for bidirectional completion
    op.add_column('contracts', sa.Column('platform_fee', sa.Numeric(10, 2), nullable=False, server_default='0'))
    op.add_column('contracts', sa.Column('settlement_amount', sa.Numeric(10, 2), nullable=False, server_default='0'))
    op.add_column('contracts', sa.Column('studio_confirmed_at', sa.DateTime(), nullable=True))
    op.add_column('contracts', sa.Column('instructor_confirmed_at', sa.DateTime(), nullable=True))
    op.add_column('contracts', sa.Column('policy_agreed_at', sa.DateTime(), nullable=True))
    op.add_column('contracts', sa.Column('policy_version', sa.String(10), nullable=True))

    # Create disputes table
    op.create_table('disputes',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('contract_id', GUID(), nullable=False),
        sa.Column('reported_by', GUID(), nullable=False),
        sa.Column('reported_against', GUID(), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('objection_deadline', sa.DateTime(), nullable=True),
        sa.Column('objection_reason', sa.Text(), nullable=True),
        sa.Column('resolution', sa.String(20), nullable=True),
        sa.Column('resolution_reason', sa.Text(), nullable=True),
        sa.Column('resolved_by', sa.String(50), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('evidence_snapshot', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reported_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reported_against'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_disputes_status', 'disputes', ['status'])
    op.create_index('idx_disputes_contract_id', 'disputes', ['contract_id'])
    op.create_index('idx_disputes_deadline', 'disputes', ['objection_deadline'],
                     postgresql_where=sa.text("status = 'open'"))

    # Create user_churn_logs table
    op.create_table('user_churn_logs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('event_type', sa.String(20), nullable=False),
        sa.Column('reason_code', sa.String(50), nullable=True),
        sa.Column('reason_detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_churn_logs_user_id', 'user_churn_logs', ['user_id'])
    op.create_index('idx_user_churn_logs_event_type', 'user_churn_logs', ['event_type'])

    # Create policy_agreements table
    op.create_table('policy_agreements',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('policy_type', sa.String(50), nullable=False),
        sa.Column('policy_version', sa.String(10), nullable=False),
        sa.Column('agreed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_policy_agreements_user_id', 'policy_agreements', ['user_id'])

    # Add indexes for improved performance
    op.create_index('idx_users_last_active', 'users', ['last_active_at'])
    op.create_index('idx_users_trust_score', 'users', ['trust_score'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_users_trust_score', 'users')
    op.drop_index('idx_users_last_active', 'users')
    op.drop_index('idx_policy_agreements_user_id', 'policy_agreements')
    op.drop_index('idx_user_churn_logs_event_type', 'user_churn_logs')
    op.drop_index('idx_user_churn_logs_user_id', 'user_churn_logs')
    op.drop_index('idx_disputes_deadline', 'disputes')
    op.drop_index('idx_disputes_contract_id', 'disputes')
    op.drop_index('idx_disputes_status', 'disputes')

    # Drop tables
    op.drop_table('policy_agreements')
    op.drop_table('user_churn_logs')
    op.drop_table('disputes')

    # Remove columns from contracts
    op.drop_column('contracts', 'policy_version')
    op.drop_column('contracts', 'policy_agreed_at')
    op.drop_column('contracts', 'instructor_confirmed_at')
    op.drop_column('contracts', 'studio_confirmed_at')
    op.drop_column('contracts', 'settlement_amount')
    op.drop_column('contracts', 'platform_fee')

    # Remove columns from users
    op.drop_column('users', 'trust_score')
    op.drop_column('users', 'onboarding_completed')
    op.drop_column('users', 'last_active_at')
    op.drop_column('users', 'is_early_bird')
    op.drop_column('users', 'deposit_first_paid_at')

    # Restore default deposit to 50000
    op.execute("UPDATE users SET deposit_required = 50000 WHERE deposit_required = 30000")