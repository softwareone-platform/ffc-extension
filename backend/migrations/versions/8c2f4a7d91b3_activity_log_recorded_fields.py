"""activity_log_recorded_fields

Revision ID: 8c2f4a7d91b3
Revises: 659618534e87
Create Date: 2026-11-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision: str = '8c2f4a7d91b3'
down_revision: Union[str, None] = '659618534e87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Renames only, so that the entries are named like the audit fields of the other models
    # (`created_at` / `created_by`). No data is touched.
    op.alter_column('activity_logs', 'timestamp', new_column_name='recorded_at')
    op.alter_column('activity_logs', 'actor_id', new_column_name='recorded_by')
    op.execute('ALTER INDEX ix_activity_logs_timestamp RENAME TO ix_activity_logs_recorded_at')
    op.execute('ALTER INDEX ix_activity_logs_actor_id RENAME TO ix_activity_logs_recorded_by')
    op.execute(
        'ALTER TABLE activity_logs '
        'RENAME CONSTRAINT fk_activity_logs_actor_id_actors TO fk_activity_logs_recorded_by_actors'
    )


def downgrade() -> None:
    op.execute(
        'ALTER TABLE activity_logs '
        'RENAME CONSTRAINT fk_activity_logs_recorded_by_actors TO fk_activity_logs_actor_id_actors'
    )
    op.execute('ALTER INDEX ix_activity_logs_recorded_by RENAME TO ix_activity_logs_actor_id')
    op.execute('ALTER INDEX ix_activity_logs_recorded_at RENAME TO ix_activity_logs_timestamp')
    op.alter_column('activity_logs', 'recorded_by', new_column_name='actor_id')
    op.alter_column('activity_logs', 'recorded_at', new_column_name='timestamp')
