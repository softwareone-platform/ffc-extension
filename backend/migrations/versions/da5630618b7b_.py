"""empty message

Revision ID: da5630618b7b
Revises: 5d1088615729, b3e1f0a6c9d2
Create Date: 2026-11-23 08:35:58.576854

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = 'da5630618b7b'
down_revision: Union[str, None] = ('5d1088615729', 'b3e1f0a6c9d2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
