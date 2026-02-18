"""Add Trust Score fields

Revision ID: 007_add_trust_score
Revises: 006_deposit_deprecation
Create Date: 2026-02-18

Add trust_score and trust_level fields to users table for v3.0 trust system.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_add_trust_score'
down_revision = '006_deposit_deprecation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add trust score fields to users table."""
    # Add trust_score column (0-100)
    op.add_column('users',
        sa.Column('trust_score', sa.Integer(), nullable=False, server_default='40')
    )

    # Add trust_level column
    op.add_column('users',
        sa.Column('trust_level', sa.String(20), nullable=False, server_default='신진')
    )

    # Add index for trust_score for efficient sorting
    op.create_index('ix_users_trust_score', 'users', ['trust_score'], unique=False)

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
                ELSE '신진'
            END
    """)


def downgrade() -> None:
    """Remove trust score fields."""
    op.drop_index('ix_users_trust_score', table_name='users')
    op.drop_column('users', 'trust_level')
    op.drop_column('users', 'trust_score')