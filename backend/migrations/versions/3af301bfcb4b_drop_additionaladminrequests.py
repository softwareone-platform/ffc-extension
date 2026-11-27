"""drop_additionaladminrequests

Copy every add-admin request into the Activity Log as a completed
`organization.admin_added` entry, then drop `additionaladminrequests`.

Revision ID: 3af301bfcb4b
Revises: 8c2f4a7d91b3
Create Date: 2026-11-27 12:00:00.000000

"""
import random
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db.constants import APP_ACTOR_ID


# revision identifiers, used by Alembic.
revision: str = '3af301bfcb4b'
down_revision: Union[str, None] = '8c2f4a7d91b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Lightweight tables with only the columns involved: the models may change after this
# migration, and `AdditionalAdminRequest` no longer exists.
additional_admin_requests = sa.table(
    'additionaladminrequests',
    sa.column('id', sa.String()),
    sa.column('email', sa.String()),
    sa.column('display_name', sa.String()),
    sa.column('notes', sa.Text()),
    sa.column('organization_id', sa.String()),
    sa.column('created_by', sa.String()),
    sa.column('created_at', sa.DateTime(timezone=True)),
)
organizations = sa.table(
    'organizations',
    sa.column('id', sa.String()),
    sa.column('name', sa.String()),
)
activity_logs = sa.table(
    'activity_logs',
    sa.column('id', sa.String()),
    sa.column('recorded_at', sa.DateTime(timezone=True)),
    sa.column('recorded_by', sa.String()),
    sa.column('action', sa.String()),
    sa.column('message', sa.Text()),
    sa.column('status', sa.String()),
    sa.column('operation_key', sa.String()),
)


def _new_activity_log_id(connection: sa.Connection, taken: set[str]) -> str:
    """A free `FLOG-xxxx-xxxx-xxxx` id, as `HumanReadablePKMixin` generates it."""
    while True:
        digits = f"{random.randint(10**11, 10**12 - 1)}"  # noqa: S311
        entry_id = f"FLOG-{digits[0:4]}-{digits[4:8]}-{digits[8:12]}"
        if entry_id in taken:
            continue
        if connection.scalar(sa.select(sa.exists().where(activity_logs.c.id == entry_id))):
            continue
        taken.add(entry_id)
        return entry_id


def upgrade() -> None:
    connection = op.get_bind()
    requests = connection.execute(
        sa.select(
            additional_admin_requests.c.email,
            additional_admin_requests.c.display_name,
            additional_admin_requests.c.notes,
            additional_admin_requests.c.created_by,
            additional_admin_requests.c.created_at,
            organizations.c.id.label('organization_id'),
            organizations.c.name.label('organization_name'),
        )
        .join(organizations, organizations.c.id == additional_admin_requests.c.organization_id)
        .order_by(additional_admin_requests.c.created_at, additional_admin_requests.c.id)
    ).all()

    # One completed entry per request, as `POST /organizations/{id}/add-admin` now records
    # it: same action, key and final message. No notes and no change records.
    taken: set[str] = set()
    entries = [
        {
            'id': _new_activity_log_id(connection, taken),
            'recorded_at': request.created_at,
            'recorded_by': request.created_by or APP_ACTOR_ID,
            'action': 'organization.admin_added',
            'message': (
                f"'{request.display_name}' ({request.email}) added as admin of "
                f"'{request.organization_name}' ({request.organization_id}). "
                f"Reason: {request.notes}"
            ),
            'status': 'completed',
            'operation_key': f"add-admin:{request.organization_id}:{request.email.lower()}",
        }
        for request in requests
    ]
    if entries:
        op.bulk_insert(activity_logs, entries)

    op.drop_index(op.f('ix_additionaladminrequests_id'), table_name='additionaladminrequests')
    op.drop_table('additionaladminrequests')


def downgrade() -> None:
    # The table comes back empty: the requests stay in the Activity Log as entries.
    op.create_table('additionaladminrequests',
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('notes', sa.Text(), nullable=False),
    sa.Column('display_name', sa.String(length=255), nullable=False),
    sa.Column('organization_id', sa.String(), nullable=False),
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('deleted_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['actors.id'], ),
    sa.ForeignKeyConstraint(['deleted_by'], ['actors.id'], ),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    sa.ForeignKeyConstraint(['updated_by'], ['actors.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_additionaladminrequests_id'), 'additionaladminrequests', ['id'], unique=True)
