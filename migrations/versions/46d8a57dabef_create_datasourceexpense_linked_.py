"""Create DatasourceExpense.linked_datasource_id and linked_datasource_type

Revision ID: 46d8a57dabef
Revises: 7cd884694384
Create Date: 2025-05-12 13:54:33.330961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = '0fcca0cf1151'
down_revision: Union[str, None] = '7cd884694384'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the existing unique constraint as it doesn't include the datasource type
    op.drop_constraint('uq_datasource_expenses_per_month', 'datasource_expenses', type_='unique')
    
    # Add the new columns with nullable=True as there are existing rows
    op.add_column('datasource_expenses', sa.Column('linked_datasource_id', sa.String(length=255), nullable=True))
    op.add_column('datasource_expenses', sa.Column('linked_datasource_type', sa.Enum('aws_cnr', 'azure_cnr', 'azure_tenant', 'gcp_cnr', 'unknown', name='datasourcetype'), nullable=True))
    
    # Set the default values for existing rows to an empty string or 'unknown' for datasource_type
    op.execute(sa.text("UPDATE datasource_expenses SET linked_datasource_id = ''"))
    op.execute(sa.text("UPDATE datasource_expenses SET linked_datasource_type = 'unknown'"))

    # Remove the nullable constraints now that all existing rows have a value
    op.alter_column('datasource_expenses', 'linked_datasource_id', existing_type=sa.String(length=255), nullable=False)
    op.alter_column('datasource_expenses', 'linked_datasource_type', existing_type=sa.Enum('aws_cnr', 'azure_cnr', 'azure_tenant', 'gcp_cnr', 'unknown', name='datasourcetype'), nullable=False)
    
    # Re-add the constraint (now also including the linked datasource type) once all the new columns
    # populated and non-nullab le
    op.create_unique_constraint('uq_datasource_expenses_per_month', 'datasource_expenses', ['datasource_id', 'linked_datasource_type', 'organization_id', 'year', 'month'])
    


def downgrade() -> None:
    # Drop the constraint as it has a reference to the linked datasource type which is being removed
    op.drop_constraint('uq_datasource_expenses_per_month', 'datasource_expenses', type_='unique')
    
    # Drop the new columns
    op.drop_column('datasource_expenses', 'linked_datasource_type')
    op.drop_column('datasource_expenses', 'linked_datasource_id')
    
    # Re-add the original constraint (without the linked datasource type)
    op.create_unique_constraint('uq_datasource_expenses_per_month', 'datasource_expenses', ['datasource_id', 'organization_id', 'year', 'month'])
