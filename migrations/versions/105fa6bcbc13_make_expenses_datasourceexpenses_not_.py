"""Make expenses DatasourceExpenses not nullable

Revision ID: 105fa6bcbc13
Revises: 75971b70c7de
Create Date: 2025-08-26 14:46:25.820605

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = '105fa6bcbc13'
down_revision: Union[str, None] = '75971b70c7de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Setting all null expenses to 0.0000
    op.execute("UPDATE datasource_expenses SET expenses = CAST(0.0000 AS NUMERIC(10,4)) WHERE expenses IS NULL")
    # Make expenses column not nullable
    op.alter_column('datasource_expenses', 'expenses',
               existing_type=sa.NUMERIC(precision=18, scale=4),
               server_default='0.0000', nullable=False)


def downgrade() -> None:
    # Make expenses column nullable
    op.alter_column('datasource_expenses', 'expenses',
               existing_type=sa.NUMERIC(precision=18, scale=4),
               nullable=True)
