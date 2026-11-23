"""add_focus_datasource_type

Revision ID: b3e1f0a6c9d2
Revises: 294f7a8587f3
Create Date: 2026-11-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b3e1f0a6c9d2'
down_revision: Union[str, None] = '294f7a8587f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # `datasourcetype` backs both `entitlements.linked_datasource_type` and
    # `datasource_expenses.linked_datasource_type`: adding the value to the type covers both.
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block on PostgreSQL < 12 and is
    # not transactional on newer versions either, so commit the pending transaction first.
    with op.get_context().autocommit_block():
        # `gcp_tenant` exists in the Python enum but was never added to the database type.
        op.execute("ALTER TYPE datasourcetype ADD VALUE IF NOT EXISTS 'gcp_tenant'")
        op.execute("ALTER TYPE datasourcetype ADD VALUE IF NOT EXISTS 'focus'")


def downgrade() -> None:
    # PostgreSQL has no ALTER TYPE ... DROP VALUE: removing an enum value would require
    # rebuilding the type and rewriting every column that uses it.
    print(
        "WARNING: Cannot safely downgrade enum values 'focus' and 'gcp_tenant' from "
        "'datasourcetype'. Manual intervention required."
    )
