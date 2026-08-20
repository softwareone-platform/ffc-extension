"""Organization terminate status

Revision ID: 0b76abbc8976
Revises: 91e67d9ca2be
Create Date: 2026-08-14 17:09:47.779462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = '0b76abbc8976'
down_revision: Union[str, None] = '91e67d9ca2be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('organizations', sa.Column('terminated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('organizations', sa.Column('terminated_by_id', sa.String(), nullable=True))
    op.create_foreign_key(op.f('fk_organizations_terminated_by_id_actors'), 'organizations', 'actors', ['terminated_by_id'], ['id'])
    op.execute("ALTER TYPE organizationstatus RENAME VALUE 'cancelled' TO 'terminated'")
    op.execute(
        "UPDATE organizations "
        "SET status = 'terminated', "
        "terminated_at = deleted_at, "
        "deleted_at = NULL "
        "WHERE status = 'deleted'"
    )

def downgrade() -> None:
    op.execute("ALTER TYPE organizationstatus RENAME VALUE 'terminated' TO 'cancelled'")
    op.drop_constraint(op.f('fk_organizations_terminated_by_id_actors'), 'organizations', type_='foreignkey')
    op.drop_column('organizations', 'terminated_by_id')
    op.drop_column('organizations', 'terminated_at')
