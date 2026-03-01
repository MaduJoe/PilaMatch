"""Trust Tier system: penalty_records, payment_confirmations, user tier fields

- Create penalty_records table
- Create payment_confirmations table
- Add tier, tier_computed_at, suspension_until, restriction_until to users
- Add location_proof_verified to studio_profiles
- Add payment_method, terms_agreed to job_posts
- Data migration: set initial tier for existing users

Revision ID: 016_trust_tier
Revises: 015_pivot_urgent_sub
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa

revision = '016_trust_tier'
down_revision = '015_pivot_urgent_sub'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- penalty_records -------------------------------------------------------
    op.create_table(
        'penalty_records',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('user_id', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('penalty_type', sa.String(30), nullable=False, index=True),
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('reported_by', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('suspend_until', sa.DateTime(), nullable=True),
        sa.Column('restrict_until', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('evidence_snapshot', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # -- payment_confirmations -------------------------------------------------
    op.create_table(
        'payment_confirmations',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('application_id', sa.CHAR(36), sa.ForeignKey('applications.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('center_user_id', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('instructor_user_id', sa.CHAR(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('status', sa.String(20), server_default='pending', nullable=False),
        sa.Column('center_marked_paid_at', sa.DateTime(), nullable=True),
        sa.Column('instructor_confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('dispute_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # -- users: tier fields ----------------------------------------------------
    op.add_column('users', sa.Column('tier', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('tier_computed_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('suspension_until', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('restriction_until', sa.DateTime(), nullable=True))

    # -- studio_profiles: location proof ---------------------------------------
    op.add_column('studio_profiles', sa.Column('location_proof_verified', sa.Boolean(), server_default='0', nullable=False))

    # -- job_posts: payment method + terms -------------------------------------
    op.add_column('job_posts', sa.Column('payment_method', sa.String(50), nullable=True))
    op.add_column('job_posts', sa.Column('terms_agreed', sa.Boolean(), server_default='0', nullable=False))

    # -- Data migration: set initial tier for existing users -------------------
    op.execute(
        "UPDATE users SET tier = 't1_basic' WHERE role = 'instructor' AND tier IS NULL"
    )
    op.execute(
        "UPDATE users SET tier = 'c1_basic' WHERE role = 'studio' AND tier IS NULL"
    )


def downgrade() -> None:
    # -- job_posts -------------------------------------------------------------
    op.drop_column('job_posts', 'terms_agreed')
    op.drop_column('job_posts', 'payment_method')

    # -- studio_profiles -------------------------------------------------------
    op.drop_column('studio_profiles', 'location_proof_verified')

    # -- users -----------------------------------------------------------------
    op.drop_column('users', 'restriction_until')
    op.drop_column('users', 'suspension_until')
    op.drop_column('users', 'tier_computed_at')
    op.drop_column('users', 'tier')

    # -- tables ----------------------------------------------------------------
    op.drop_table('payment_confirmations')
    op.drop_table('penalty_records')
