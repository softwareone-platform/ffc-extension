"""backfill_audit_actors

Revision ID: 5d1088615729
Revises: 294f7a8587f3
Create Date: 2026-11-19 17:34:46.584181

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db.constants import APP_ACTOR_ID
from app.db.models import AuditableMixin, Base


# revision identifiers, used by Alembic.
revision: str = '5d1088615729'
down_revision: Union[str, None] = '294f7a8587f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rows written outside a request (commands, event handlers) were left without an audit
    # actor. Attribute them to the application itself (seeded by 9f033317274c_add_activity_log).
    #
    # The tables come from the models, not from a hand-written list or the database catalog:
    # every mapped class inheriting AuditableMixin is backfilled.
    for mapper in sorted(Base.registry.mappers, key=lambda mapper: mapper.class_.__name__):
        if not issubclass(mapper.class_, AuditableMixin):
            continue

        # A lightweight table with only the columns involved, instead of the model's table:
        # the model's `updated_at` has an `onupdate` that would add itself to every UPDATE.
        # This way `updated_at` is not part of the statement at all.
        table = sa.table(
            mapper.columns["created_by_id"].table.name,
            sa.column(mapper.columns["created_by_id"].name),
            sa.column(mapper.columns["updated_by_id"].name),
            sa.column(mapper.columns["deleted_by_id"].name),
            sa.column(mapper.columns["deleted_at"].name),
        )
        created_by, updated_by, deleted_by, deleted_at = table.columns

        for column, condition in (
            (created_by, created_by.is_(None)),
            (updated_by, updated_by.is_(None)),
            # Only soft-deleted rows get a deleted_by: on a live row NULL means "not deleted".
            (deleted_by, sa.and_(deleted_by.is_(None), deleted_at.is_not(None))),
        ):
            op.execute(sa.update(table).where(condition).values({column.name: APP_ACTOR_ID}))


def downgrade() -> None:
    # Not reversible: after the backfill an originally NULL value cannot be told apart from
    # a row that was really written by the application.
    pass
