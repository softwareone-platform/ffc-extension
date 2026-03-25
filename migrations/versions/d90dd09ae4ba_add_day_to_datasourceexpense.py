"""Add day to DatasourceExpense

Revision ID: d90dd09ae4ba
Revises: 0fcca0cf1151
Create Date: 2025-05-28 15:28:32.360911

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = 'd90dd09ae4ba'
down_revision: Union[str, None] = '0fcca0cf1151'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing unique constraint as it doesn't include day
    op.execute('DELETE FROM datasource_expenses')
    op.drop_constraint('uq_datasource_expenses_per_month', 'datasource_expenses', type_='unique')

    # Add new column day with nullable=False and set default value 1 to existing rows
    op.add_column('datasource_expenses', sa.Column('day', sa.Integer(), nullable=True))
    op.alter_column('datasource_expenses', 'day', nullable=False)

    # Rename column month_expenses, set nullable=False and empty values to 0.0
    op.alter_column('datasource_expenses', 'month_expenses', new_column_name='expenses')
    op.execute('UPDATE datasource_expenses SET expenses = 0.00 WHERE expenses IS NULL')
    op.alter_column('datasource_expenses', 'expenses', nullable=False)

    # Re-add constraint including day
    op.create_unique_constraint(
        'uq_datasource_expenses_per_day',
        'datasource_expenses',
        ['datasource_id', 'linked_datasource_type', 'organization_id', 'year', 'month', 'day']
    )


def downgrade() -> None:
    # Drop the constraints because day column will be dropped
    op.drop_constraint('uq_datasource_expenses_per_day', 'datasource_expenses', type_='unique')

    # Rename back to month_expenses and remove nullable=False
    op.alter_column('datasource_expenses', 'expenses', new_column_name='month_expenses')
    op.alter_column('datasource_expenses', 'month_expenses', nullable=True)

    # Drop day column
    op.drop_column('datasource_expenses', 'day')

    # Return previous constraint
    op.create_unique_constraint(
        'uq_datasource_expenses_per_month',
        'datasource_expenses',
        ['datasource_id', 'linked_datasource_type', 'organization_id', 'year', 'month']
    )
