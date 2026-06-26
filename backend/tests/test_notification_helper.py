import json

import httpx
import pytest
from freezegun import freeze_time
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture, MockType

from app.billing.dataclasses import ProcessResultInfo
from app.billing.enum import ProcessResult
from app.billing.notification_helper import (
    MAX_MESSAGE_CHARS,
    check_results,
    send_notifications,
)

# Skip the inter-message pacing delay for every test in this file; chunked
# sends would otherwise block on the real sleep between messages.
pytestmark = pytest.mark.usefixtures("_no_msteams_pacing")


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


def _posted_titles(requests: list[httpx.Request]) -> list[str]:
    """Extract the card title from each POST request's compact-JSON body."""
    titles: list[str] = []
    for request in requests:
        parsed = json.loads(request.content)
        titles.append(parsed["attachments"][0]["content"]["body"][0]["text"])
    return titles


def _posted_card_rows(requests: list[httpx.Request]) -> list[list[tuple[str, ...]]]:
    """Extract the data rows from each POST request's body. Returns one list of
    rows per posted message."""
    chunks: list[list[tuple[str, ...]]] = []
    for request in requests:
        parsed = json.loads(request.content)
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
    configured_webhook: MockType, httpx_mock: HTTPXMock
) -> None:
    """A large success result set must produce more than one real HTTP POST
    to the configured Teams webhook, with each message titled `(i of N)`."""
    httpx_mock.add_response(
        method="POST",
        url=configured_webhook.msteams_notifications_webhook_url,
        status_code=202,
        is_reusable=True,
    )
    results = _make_results(count=80, result=ProcessResult.JOURNAL_GENERATED)

    await send_notifications(results=results, year=2025, month=9)

    requests = httpx_mock.get_requests()
    total = len(requests)
    assert total > 1, f"expected multiple POSTs, got {total}"

    titles = _posted_titles(requests)
    for idx, title in enumerate(titles, start=1):
        assert f"({idx} of {total})" in title


@freeze_time("2025-09-08")
async def test_send_notifications_error_splits_into_multiple_messages(
    configured_webhook: MockType, httpx_mock: HTTPXMock
) -> None:
    """A large error result set (after the cutoff day) must split into
    multiple ERROR notifications, all really sent to Teams."""
    httpx_mock.add_response(
        method="POST",
        url=configured_webhook.msteams_notifications_webhook_url,
        status_code=202,
        is_reusable=True,
    )
    results = _make_results(count=80, result=ProcessResult.ERROR)

    await send_notifications(results=results, year=2025, month=9, cutoff_day=5)

    requests = httpx_mock.get_requests()
    total = len(requests)
    assert total > 1

    titles = _posted_titles(requests)
    for idx, title in enumerate(titles, start=1):
        assert f"({idx} of {total})" in title
        assert "completed with Errors" in title


@freeze_time("2025-09-01")
async def test_send_notifications_in_progress_splits_into_multiple_messages(
    configured_webhook: MockType, httpx_mock: HTTPXMock
) -> None:
    """Before the cutoff day, errors are reported as IN_PROGRESS and must
    still be chunked across multiple real messages."""
    httpx_mock.add_response(
        method="POST",
        url=configured_webhook.msteams_notifications_webhook_url,
        status_code=202,
        is_reusable=True,
    )
    results = _make_results(count=80, result=ProcessResult.ERROR)

    await send_notifications(results=results, year=2025, month=9, cutoff_day=5)

    requests = httpx_mock.get_requests()
    total = len(requests)
    assert total > 1

    titles = _posted_titles(requests)
    for idx, title in enumerate(titles, start=1):
        assert f"({idx} of {total})" in title
        assert "in progress" in title


async def test_send_notifications_small_payload_sends_single_message(
    configured_webhook: MockType, httpx_mock: HTTPXMock
) -> None:
    """A small result set must produce exactly one real HTTP POST and the
    title must NOT contain a `(i of N)` suffix."""
    httpx_mock.add_response(
        method="POST",
        url=configured_webhook.msteams_notifications_webhook_url,
        status_code=202,
        is_reusable=True,
    )
    results = _make_results(count=2, result=ProcessResult.JOURNAL_GENERATED, message_size=20)

    await send_notifications(results=results, year=2025, month=9)

    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    titles = _posted_titles(requests)
    assert " of " not in titles[0]


async def test_send_notifications_each_part_carries_subset_of_rows(
    configured_webhook: MockType, httpx_mock: HTTPXMock
) -> None:
    """Every authorization_id in the input must appear in exactly one of
    the sent messages, with no duplicates and no losses across the chunks."""
    httpx_mock.add_response(
        method="POST",
        url=configured_webhook.msteams_notifications_webhook_url,
        status_code=202,
        is_reusable=True,
    )
    results = _make_results(count=80, result=ProcessResult.JOURNAL_GENERATED)
    expected_auth_ids = {r.authorization_id for r in results}

    await send_notifications(results=results, year=2025, month=9)

    requests = httpx_mock.get_requests()
    assert len(requests) > 1

    seen: list[str] = []
    for chunk in _posted_card_rows(requests):
        for row in chunk:
            seen.append(row[0])

    assert sorted(seen) == sorted(expected_auth_ids), (
        "each authorization_id should appear in exactly one part"
    )


async def test_send_notifications_truncates_long_message(
    configured_webhook: MockType, httpx_mock: HTTPXMock
) -> None:
    """Messages longer than MAX_MESSAGE_CHARS must be truncated before they
    reach the rendered row, so any content past the cap never lands in Teams."""
    httpx_mock.add_response(
        method="POST",
        url=configured_webhook.msteams_notifications_webhook_url,
        status_code=202,
        is_reusable=True,
    )
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

    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    chunks = _posted_card_rows(requests)
    rendered_message = chunks[0][0][3]
    assert sentinel not in rendered_message


# ---------------------------------------------------------------------------
# - check_results()
# ---------------------------------------------------------------------------


def test_check_results_no_errors(process_result_success_payload: list[ProcessResultInfo]) -> None:
    success, fail = check_results(results=process_result_success_payload)
    assert success is True
    assert fail is False


def test_check_results_journal_skipped(
    process_result_with_warning: list[ProcessResultInfo],
) -> None:
    success, fail = check_results(results=process_result_with_warning)
    assert success is False
    assert fail is False


def test_check_results_error(process_result_with_error: list[ProcessResultInfo]) -> None:
    success, fail = check_results(results=process_result_with_error)
    assert success is False
    assert fail is True


# ---------------------------------------------------------------------------
# - send_notifications() cycle log messages
# ---------------------------------------------------------------------------


async def test_send_notifications_success_notifies(
    mocker: MockerFixture,
    process_result_success_payload: list[ProcessResultInfo],
) -> None:
    send_notification_mock = mocker.patch(
        "app.notifications.send_notification", new_callable=mocker.AsyncMock
    )

    await send_notifications(results=process_result_success_payload, year=2025, month=9)

    assert send_notification_mock.called


@freeze_time("2025-09-01")
async def test_send_notifications_in_progress_logs_cycle(
    mocker: MockerFixture,
    process_result_with_error: list[ProcessResultInfo],
    caplog: pytest.LogCaptureFixture,
) -> None:
    send_notification_mock = mocker.patch(
        "app.notifications.send_notification", new_callable=mocker.AsyncMock
    )

    with caplog.at_level("WARNING"):
        await send_notifications(results=process_result_with_error, year=2025, month=9)
    assert send_notification_mock.called
    assert "Journals for the September-2025 billing cycle are in progress." in caplog.messages[0]


@freeze_time("2025-09-08")
async def test_send_notifications_error_logs_cycle(
    mocker: MockerFixture,
    process_result_with_error: list[ProcessResultInfo],
    caplog: pytest.LogCaptureFixture,
) -> None:
    send_notification_mock = mocker.patch(
        "app.notifications.send_notification", new_callable=mocker.AsyncMock
    )

    with caplog.at_level("ERROR"):
        await send_notifications(results=process_result_with_error, year=2025, month=9)
    assert send_notification_mock.called
    assert "The billing process for September-2025 was completed with Errors." in caplog.messages[0]
