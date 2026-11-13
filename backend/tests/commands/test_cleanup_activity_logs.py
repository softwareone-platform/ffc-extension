import logging
from datetime import UTC, datetime, timedelta

import pytest
import time_machine
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner

from app.cli import app
from app.commands import cleanup_activity_logs
from app.conf import Settings
from app.db.models import ActivityLog, ChangeRecord
from tests.types import ModelFactory

NOW = datetime(2026, 11, 13, 10, 0, tzinfo=UTC)
DEFAULT_CUTOFF = NOW - timedelta(days=730)


async def get_remaining_activity_log_ids(db_session: AsyncSession) -> set[str]:
    """Return the ids of the activity log entries still in the database."""
    return set((await db_session.scalars(select(ActivityLog.id))).all())


def test_activity_log_retention_defaults_to_two_years(test_settings: Settings) -> None:
    """The activity log retention period defaults to 730 days."""
    assert test_settings.activity_log_retention_days == 730


@time_machine.travel(NOW, tick=False)
async def test_main_deletes_entries_older_than_default_retention(
    db_session: AsyncSession,
    test_settings: Settings,
    activity_log_factory: ModelFactory[ActivityLog],
) -> None:
    """Entries older than the default 730 days retention are deleted, newer ones are kept."""
    just_outside = await activity_log_factory(timestamp=DEFAULT_CUTOFF - timedelta(seconds=1))
    very_old = await activity_log_factory(timestamp=NOW - timedelta(days=2000))
    at_cutoff = await activity_log_factory(timestamp=DEFAULT_CUTOFF)
    just_inside = await activity_log_factory(timestamp=DEFAULT_CUTOFF + timedelta(seconds=1))
    recent = await activity_log_factory(timestamp=NOW)

    await cleanup_activity_logs.main(test_settings)

    remaining = await get_remaining_activity_log_ids(db_session)
    assert remaining == {at_cutoff.id, just_inside.id, recent.id}
    assert just_outside.id not in remaining
    assert very_old.id not in remaining


@time_machine.travel(NOW, tick=False)
async def test_main_deletes_entries_older_than_custom_retention(
    db_session: AsyncSession,
    test_settings: Settings,
    activity_log_factory: ModelFactory[ActivityLog],
) -> None:
    """A custom retention period overrides the default when selecting entries to delete."""
    settings = test_settings.model_copy(update={"activity_log_retention_days": 30})
    cutoff = NOW - timedelta(days=30)
    await activity_log_factory(timestamp=cutoff - timedelta(seconds=1))
    just_inside = await activity_log_factory(timestamp=cutoff + timedelta(seconds=1))
    recent = await activity_log_factory(timestamp=NOW)

    await cleanup_activity_logs.main(settings)

    assert await get_remaining_activity_log_ids(db_session) == {just_inside.id, recent.id}


@time_machine.travel(NOW, tick=False)
async def test_main_cascades_deletion_to_change_records(
    db_session: AsyncSession,
    test_settings: Settings,
    activity_log_factory: ModelFactory[ActivityLog],
    change_record_factory: ModelFactory[ChangeRecord],
) -> None:
    """Change records of deleted entries are removed, those of kept entries are untouched."""
    old_log = await activity_log_factory(timestamp=NOW - timedelta(days=800))
    await change_record_factory(activity_log=old_log)
    await change_record_factory(activity_log=old_log)
    recent_log = await activity_log_factory(timestamp=NOW - timedelta(days=10))
    kept_record = await change_record_factory(activity_log=recent_log)

    await cleanup_activity_logs.main(test_settings)

    remaining_records = (await db_session.scalars(select(ChangeRecord.id))).all()
    assert remaining_records == [kept_record.id]


@time_machine.travel(NOW, tick=False)
async def test_main_deletes_in_batches(
    db_session: AsyncSession,
    test_settings: Settings,
    caplog: pytest.LogCaptureFixture,
    activity_log_factory: ModelFactory[ActivityLog],
) -> None:
    """Expired entries are deleted in batches no larger than the configured batch size."""
    settings = test_settings.model_copy(update={"activity_log_cleanup_batch_size": 2})
    for days in range(800, 805):
        await activity_log_factory(timestamp=NOW - timedelta(days=days))
    recent = await activity_log_factory(timestamp=NOW)

    with caplog.at_level(logging.DEBUG, logger=cleanup_activity_logs.__name__):
        await cleanup_activity_logs.main(settings)

    batch_messages = [m for m in caplog.messages if m.startswith("Deleted a batch")]
    assert batch_messages == [
        "Deleted a batch of 2 activity log entries",
        "Deleted a batch of 2 activity log entries",
        "Deleted a batch of 1 activity log entries",
    ]
    assert await get_remaining_activity_log_ids(db_session) == {recent.id}


@time_machine.travel(NOW, tick=False)
async def test_main_logs_number_of_deleted_entries(
    test_settings: Settings,
    caplog: pytest.LogCaptureFixture,
    activity_log_factory: ModelFactory[ActivityLog],
) -> None:
    """Each run logs the cutoff and the total number of deleted entries."""
    await activity_log_factory(timestamp=NOW - timedelta(days=800))
    await activity_log_factory(timestamp=NOW - timedelta(days=900))

    with caplog.at_level(logging.INFO, logger=cleanup_activity_logs.__name__):
        await cleanup_activity_logs.main(test_settings)

    assert caplog.messages == [
        "Deleting activity log entries older than 2024-11-13T10:00:00+00:00 "
        "(retention period: 730 days)",
        "2 activity log entries older than 2024-11-13T10:00:00+00:00 have been deleted",
    ]


@time_machine.travel(NOW, tick=False)
async def test_main_logs_zero_when_nothing_to_delete(
    test_settings: Settings,
    caplog: pytest.LogCaptureFixture,
    activity_log_factory: ModelFactory[ActivityLog],
) -> None:
    """A run with no expired entries logs that zero entries were deleted."""
    await activity_log_factory(timestamp=NOW)

    with caplog.at_level(logging.INFO, logger=cleanup_activity_logs.__name__):
        await cleanup_activity_logs.main(test_settings)

    assert caplog.messages[-1] == (
        "0 activity log entries older than 2024-11-13T10:00:00+00:00 have been deleted"
    )


@time_machine.travel(NOW, tick=False)
async def test_main_logs_and_reraises_on_error(
    mocker: MockerFixture,
    test_settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A failing batch is logged with the entries deleted so far and the error is re-raised."""
    settings = test_settings.model_copy(update={"activity_log_cleanup_batch_size": 2})
    mocker.patch(
        "app.commands.cleanup_activity_logs.delete_batch",
        side_effect=[2, RuntimeError("database unavailable")],
    )

    with (
        caplog.at_level(logging.INFO, logger=cleanup_activity_logs.__name__),
        pytest.raises(RuntimeError, match="database unavailable"),
    ):
        await cleanup_activity_logs.main(settings)

    assert caplog.records[-1].levelno == logging.ERROR
    assert caplog.messages[-1] == (
        "Failed to delete activity log entries older than 2024-11-13T10:00:00+00:00, "
        "2 entries were deleted before the failure"
    )


def test_command_runs_main_with_settings(mocker: MockerFixture, test_settings: Settings) -> None:
    """The `cleanup-activity-logs` CLI command runs `main` with the application settings."""
    mock_main_coro = mocker.MagicMock()
    mock_main = mocker.MagicMock(return_value=mock_main_coro)
    mocker.patch("app.commands.cleanup_activity_logs.main", mock_main)
    mock_run = mocker.patch("app.commands.cleanup_activity_logs.asyncio.run")

    result = CliRunner().invoke(app, ["cleanup-activity-logs"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_main_coro)
    mock_main.assert_called_once_with(test_settings)
