"""Add redeem_at to Entitlement

Revision ID: 8e6d8b9091ed
Revises: 84791d4463e8
Create Date: 2025-11-04 18:23:54.864551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = '8e6d8b9091ed'
down_revision: Union[str, None] = '84791d4463e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('entitlements', sa.Column('redeem_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('entitlements', 'redeem_at')
