"""Add Trust Score fields

Revision ID: 007_add_trust_score
Revises: 006_deposit_deprecation
Create Date: 2026-02-18

Add trust_level field and update trust_score default for v3.0 trust system.

Note: trust_score column and idx_users_trust_score index already exist from
migration 003_prdv2_updates. This migration only changes the default from
'0' to '40' and adds the new trust_level column.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_add_trust_score'
down_revision = '006_deposit_deprecation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update trust_score default and add trust_level column."""
    # trust_score column already exists from 003_prdv2_updates (default='0').
    # Change the server default from '0' to '40' for v3.0 trust system.
    op.alter_column('users', 'trust_score',
        existing_type=sa.Integer(),
        existing_nullable=False,
        server_default='40',
    )

    # Add trust_level column (new in v3.0)
    op.add_column('users',
        sa.Column('trust_level', sa.String(20), nullable=False, server_default='새싹')
    )

    # Index idx_users_trust_score already exists from 003_prdv2_updates; skip.

    # Set initial trust scores based on existing data
    # Premium users get bonus, verified users get bonus
    op.execute("""
        UPDATE users
        SET trust_score =
            CASE
                WHEN membership_tier = 'premium' THEN 50
                WHEN phone_verified = true THEN 45
                ELSE 40
            END
    """)

    op.execute("""
        UPDATE users
        SET trust_level =
            CASE
                WHEN trust_score >= 80 THEN '마스터'
                WHEN trust_score >= 60 THEN '전문'
                WHEN trust_score >= 40 THEN '인증'
                ELSE '새싹'
            END
    """)


def downgrade() -> None:
    """Remove trust_level and revert trust_score default."""
    # Drop trust_level column (owned by this migration)
    op.drop_column('users', 'trust_level')

    # Revert trust_score server default back to '0' (003_prdv2_updates value).
    # Do NOT drop the trust_score column or idx_users_trust_score index;
    # those are owned by 003_prdv2_updates.
    op.alter_column('users', 'trust_score',
        existing_type=sa.Integer(),
        existing_nullable=False,
        server_default='0',
    )