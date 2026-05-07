import json

import pytest
from freezegun import freeze_time

from app.billing.dataclasses import ProcessResultInfo
from app.billing.enum import ProcessResult
from app.billing.notification_helper import (
    MAX_MESSAGE_CHARS,
    send_notifications,
)

# Module-level: every test in this file gets the httpx mock and skips
# inter-message pacing. Equivalent to a file-scoped autouse, but the fixtures
# themselves stay opt-in at the conftest level so they don't leak into FastAPI
# integration tests that use httpx for real ASGI calls.
pytestmark = pytest.mark.usefixtures("msteams_post_mock", "_no_msteams_pacing")


def _make_results(
    count: int, result: ProcessResult, message_size: int = 400
) -> list[ProcessResultInfo]:
    """Build a list of ProcessResultInfo entries large enough to force chunking."""
    long_message = "x" * message_size
    return [
        ProcessResultInfo(
            authorization_id=f"AUTH-{i:04d}-0000",
            journal_id=f"BJO-{i:04d}-0000",
            result=result,
            message=f"{long_message} idx={i}",
        )
        for i in range(count)
    ]


def _posted_titles(post_mock) -> list[str]:
    """Extract the card title from each POST request's compact-JSON body."""
    titles: list[str] = []
    for call in post_mock.await_args_list or post_mock.call_args_list:
        body = call.kwargs.get("content")
        assert body is not None, "send_notification must POST raw bytes via content="
        parsed = json.loads(body)
        titles.append(parsed["attachments"][0]["content"]["body"][0]["text"])
    return titles


def _posted_card_rows(post_mock) -> list[list[tuple[str, ...]]]:
    """Extract the data rows from each POST request's body. Returns one list of
    rows per posted message."""
    chunks: list[list[tuple[str, ...]]] = []
    for call in post_mock.await_args_list or post_mock.call_args_list:
        body = call.kwargs.get("content")
        parsed = json.loads(body)
        body_items = parsed["attachments"][0]["content"]["body"]
        # Container is the third body item (title, text, container).
        if len(body_items) < 3:
            chunks.append([])
            continue
        container_items = body_items[2]["items"]
        # Skip the header ColumnSet (index 0); rest are data rows.
        rows: list[tuple[str, ...]] = []
        for cs in container_items[1:]:
            row = tuple(col["items"][0]["text"] for col in cs["columns"])
            rows.append(row)
        chunks.append(rows)
    return chunks


async def test_send_notifications_success_splits_into_multiple_messages(
    configured_webhook, msteams_post_mock
):
    """A large success result set must produce more than one real HTTP POST
    to the configured Teams webhook, with each message titled `(i of N)`."""
    results = _make_results(count=80, result=ProcessResult.JOURNAL_GENERATED)

    await send_notifications(results=results, year=2025, month=9)

    total = msteams_post_mock.await_count
    assert total > 1, f"expected multiple POSTs, got {total}"

    titles = _posted_titles(msteams_post_mock)
    for idx, title in enumerate(titles, start=1):
        assert f"({idx} of {total})" in title


@freeze_time("2025-09-08")
async def test_send_notifications_error_splits_into_multiple_messages(
    configured_webhook, msteams_post_mock
):
    """A large error result set (after the cutoff day) must split into
    multiple ERROR notifications, all really sent to Teams."""
    results = _make_results(count=80, result=ProcessResult.ERROR)

    await send_notifications(results=results, year=2025, month=9, cutoff_day=5)

    total = msteams_post_mock.await_count
    assert total > 1

    titles = _posted_titles(msteams_post_mock)
    for idx, title in enumerate(titles, start=1):
        assert f"({idx} of {total})" in title
        assert "completed with Errors" in title


@freeze_time("2025-09-01")
async def test_send_notifications_in_progress_splits_into_multiple_messages(
    configured_webhook, msteams_post_mock
):
    """Before the cutoff day, errors are reported as IN_PROGRESS and must
    still be chunked across multiple real messages."""
    results = _make_results(count=80, result=ProcessResult.ERROR)

    await send_notifications(results=results, year=2025, month=9, cutoff_day=5)

    total = msteams_post_mock.await_count
    assert total > 1

    titles = _posted_titles(msteams_post_mock)
    for idx, title in enumerate(titles, start=1):
        assert f"({idx} of {total})" in title
        assert "in progress" in title


async def test_send_notifications_small_payload_sends_single_message(
    configured_webhook, msteams_post_mock
):
    """A small result set must produce exactly one real HTTP POST and the
    title must NOT contain a `(i of N)` suffix."""
    results = _make_results(count=2, result=ProcessResult.JOURNAL_GENERATED, message_size=20)

    await send_notifications(results=results, year=2025, month=9)

    assert msteams_post_mock.await_count == 1
    titles = _posted_titles(msteams_post_mock)
    assert " of " not in titles[0]


async def test_send_notifications_each_part_carries_subset_of_rows(
    configured_webhook, msteams_post_mock
):
    """Every authorization_id in the input must appear in exactly one of
    the sent messages, with no duplicates and no losses across the chunks."""
    results = _make_results(count=80, result=ProcessResult.JOURNAL_GENERATED)
    expected_auth_ids = {r.authorization_id for r in results}

    await send_notifications(results=results, year=2025, month=9)

    assert msteams_post_mock.await_count > 1

    seen: list[str] = []
    for chunk in _posted_card_rows(msteams_post_mock):
        for row in chunk:
            seen.append(row[0])

    assert sorted(seen) == sorted(expected_auth_ids), (
        "each authorization_id should appear in exactly one part"
    )


async def test_send_notifications_truncates_long_message(configured_webhook, msteams_post_mock):
    """Messages longer than MAX_MESSAGE_CHARS must be truncated before they
    reach the rendered row, so any content past the cap never lands in Teams."""
    sentinel = "PAST_THE_CAP"
    results = [
        ProcessResultInfo(
            authorization_id="AUTH-0001-0000",
            journal_id="BJO-0001-0000",
            result=ProcessResult.JOURNAL_GENERATED,
            message="x" * MAX_MESSAGE_CHARS + sentinel,
        )
    ]

    await send_notifications(results=results, year=2025, month=9)

    assert msteams_post_mock.await_count == 1
    chunks = _posted_card_rows(msteams_post_mock)
    rendered_message = chunks[0][0][3]
    assert sentinel not in rendered_message
