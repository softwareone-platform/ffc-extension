"""Fix chargesfile table name and enum value

Revision ID: 7cd884694384
Revises: 6d2b289e6c92
Create Date: 2025-04-29 16:29:57.147631

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = '7cd884694384'
down_revision: Union[str, None] = '6d2b289e6c92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.rename_table('invoices', 'chargesfiles')
    op.execute("ALTER TYPE chargesfilestatus ADD VALUE IF NOT EXISTS 'processed'")


def downgrade():
    op.rename_table('chargesfiles', 'invoices')
    print("WARNING: Cannot safely downgrade enum value 'processed' from 'chargesfilestatus'. Manual intervention required.")
