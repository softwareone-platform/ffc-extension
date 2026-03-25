"""Drop ExchangeRates and ChargesFile

Revision ID: e2964d52315a
Revises: d90dd09ae4ba
Create Date: 2025-06-18 16:01:05.823569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e2964d52315a'
down_revision: Union[str, None] = 'd90dd09ae4ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.drop_index(op.f('ix_exchange_rates_id'), table_name='exchange_rates')
    op.drop_table('exchange_rates')

    op.drop_index(op.f('ix_invoices_id'), table_name='chargesfiles')
    op.drop_table('chargesfiles')


def downgrade() -> None:

    # Create a ExchangeRates table
    op.create_table('exchange_rates',
    sa.Column('api_response', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('id', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exchange_rates_id'), 'exchange_rates', ['id'], unique=True)

    # Create a ChargesFile table
    op.create_table('chargesfiles',
    sa.Column('document_date', sa.Date(), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('amount', sa.Numeric(precision=18, scale=4), nullable=True),
    sa.Column('owner_id', sa.String(), nullable=False),
    sa.Column('status', sa.Enum('draft', 'generated', 'deleted', 'processed', name='chargesfilestatus'), server_default='draft', nullable=False),
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['accounts.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoices_id'), 'chargesfiles', ['id'], unique=True)