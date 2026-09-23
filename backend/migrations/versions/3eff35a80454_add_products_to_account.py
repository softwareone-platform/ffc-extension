"""Add products to Account

Revision ID: 3eff35a80454
Revises: 0b76abbc8976
Create Date: 2026-08-27 01:09:04.927378

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = '3eff35a80454'
down_revision: Union[str, None] = '0b76abbc8976'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('accounts', sa.Column('products', sa.String(length=511), nullable=True))


def downgrade() -> None:
    op.drop_column('accounts', 'products')
