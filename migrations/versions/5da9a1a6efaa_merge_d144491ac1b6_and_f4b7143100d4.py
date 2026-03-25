"""merge d144491ac1b6 and f4b7143100d4

Revision ID: 5da9a1a6efaa
Revises: d144491ac1b6, f4b7143100d4
Create Date: 2025-03-27 10:14:52.571147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = '5da9a1a6efaa'
down_revision: Union[str, None] = ('d144491ac1b6', 'f4b7143100d4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
