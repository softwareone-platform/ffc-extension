"""Swith to daily and total expenses for DatasourceExpenses

Revision ID: 75971b70c7de
Revises: e2964d52315a
Create Date: 2025-08-15 20:01:19.536801

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = '75971b70c7de'
down_revision: Union[str, None] = 'e2964d52315a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add total_expenses column to datasource_expenses table
    op.add_column('datasource_expenses', sa.Column('total_expenses', sa.Numeric(precision=18, scale=4), nullable=True))
    # Allow null values for expenses column
    op.alter_column('datasource_expenses', 'expenses',
                    existing_type=sa.NUMERIC(precision=18, scale=4),
                    nullable=True)
    op.execute("UPDATE datasource_expenses SET total_expenses = expenses")
    op.execute("UPDATE datasource_expenses SET expenses = NULL")


def downgrade() -> None:
    # Move total_expenses values to expenses column
    op.execute("UPDATE datasource_expenses SET expenses = total_expenses")
    # Return nullable false restriction on expenses column
    op.alter_column('datasource_expenses', 'expenses',
               existing_type=sa.NUMERIC(precision=18, scale=4),
               nullable=False)
    # Drop column total_expenses from datasource_expenses table
    op.drop_column('datasource_expenses', 'total_expenses')

