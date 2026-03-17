"""add latitude longitude to studio_profiles

Revision ID: a53f4e9c1b42
Revises: 021_review_application_anchor
Create Date: 2026-03-18 02:21:42.013839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a53f4e9c1b42'
down_revision: Union[str, None] = '021_review_application_anchor'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('studio_profiles', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('studio_profiles', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('studio_profiles', 'longitude')
    op.drop_column('studio_profiles', 'latitude')
