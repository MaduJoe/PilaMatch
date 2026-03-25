"""merge: studio lat/lng + dispatch v5

Revision ID: 8afa6f26e1fa
Revises: 022_dispatch_system_v5, a53f4e9c1b42
Create Date: 2026-03-25 13:07:23.102973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8afa6f26e1fa'
down_revision: Union[str, None] = ('022_dispatch_system_v5', 'a53f4e9c1b42')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
