"""Make total_expenses DatasourceExpenses not nullable

Revision ID: 84791d4463e8
Revises: 105fa6bcbc13
Create Date: 2025-10-01 10:07:16.265241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = '84791d4463e8'
down_revision: Union[str, None] = '105fa6bcbc13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Setting all null total_expenses to expenses value
    op.execute("UPDATE datasource_expenses SET total_expenses = expenses WHERE total_expenses IS NULL")
    op.alter_column('datasource_expenses', 'total_expenses',
               existing_type=sa.NUMERIC(precision=18, scale=4),
               nullable=False)


def downgrade() -> None:
    # Make total_expenses column nullable
    op.alter_column('datasource_expenses', 'total_expenses',
               existing_type=sa.NUMERIC(precision=18, scale=4),
               nullable=True)
