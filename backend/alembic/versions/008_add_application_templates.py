"""Add application templates for Premium members (v3.0 Phase 2).

Revision ID: 008
Revises: 007
Create Date: 2026-02-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_application_templates'
down_revision = '007_add_trust_score'
branch_labels = None
depends_on = None


def upgrade():
    # Create application_templates table for Premium members
    op.create_table(
        'application_templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('usage_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Create indices
    op.create_index('ix_application_templates_user_id', 'application_templates', ['user_id'])
    op.create_index('ix_application_templates_is_default', 'application_templates', ['user_id', 'is_default'])

    # Add comment
    op.execute("COMMENT ON TABLE application_templates IS 'v3.0 Phase 2: Application templates for Premium members'")


def downgrade():
    op.drop_table('application_templates')