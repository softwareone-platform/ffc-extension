"""merge 70fa90617026 and deded05b7d54

Revision ID: b34e156283c4
Revises: 70fa90617026, deded05b7d54
Create Date: 2025-02-12 15:38:30.318552

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = 'b34e156283c4'
down_revision: Union[str, None] = ('70fa90617026', 'deded05b7d54')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
