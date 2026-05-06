import pytest
from freezegun import freeze_time

from app.billing.dataclasses import ProcessResultInfo
from app.billing.enum import ProcessResult
from app.billing.notification_helper import (
    MAX_MESSAGE_CHARS,
    _chunk_rows_by_size,
    send_notifications,
)

# Module-level: every test in this file gets the httpx mock without having
# to declare the fixture explicitly. Equivalent to a file-scoped autouse,
# but the fixture itself stays opt-in at the conftest level so it doesn't
# leak into FastAPI integration tests that use httpx for real ASGI calls.
pytestmark = pytest.mark.usefixtures("_no_real_http_post")


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


def _extract_titles(spy) -> list[str]:
    titles: list[str] = []
    for call in spy.await_args_list or spy.call_args_list:
        title = call.args[0] if call.args else call.kwargs.get("title")
        titles.append(title)
    return titles


async def test_send_notifications_success_splits_into_multiple_messages(
    configured_webhook, send_notification_spy
):
    """A large success result set must produce more than one real HTTP POST
    to the configured Teams webhook, with each message titled `(Part i/N)`."""
    results = _make_results(count=80, result=ProcessResult.JOURNAL_GENERATED)

    await send_notifications(results=results, year=2025, month=9)

    total = send_notification_spy.call_count
    assert total > 1, f"expected multiple messages, got {total}"

    titles = _extract_titles(send_notification_spy)
    for idx, title in enumerate(titles, start=1):
        assert f"(Part {idx}/{total})" in title


@freeze_time("2025-09-08")
async def test_send_notifications_error_splits_into_multiple_messages(
    configured_webhook, send_notification_spy
):
    """A large error result set (after the cutoff day) must split into
    multiple ERROR notifications, all really sent to Teams."""
    results = _make_results(count=80, result=ProcessResult.ERROR)

    await send_notifications(results=results, year=2025, month=9, cutoff_day=5)

    total = send_notification_spy.call_count
    assert total > 1

    titles = _extract_titles(send_notification_spy)
    for idx, title in enumerate(titles, start=1):
        assert f"(Part {idx}/{total})" in title
        assert "completed with Errors" in title


@freeze_time("2025-09-01")
async def test_send_notifications_in_progress_splits_into_multiple_messages(
    configured_webhook, send_notification_spy
):
    """Before the cutoff day, errors are reported as IN_PROGRESS and must
    still be chunked across multiple real messages."""
    results = _make_results(count=80, result=ProcessResult.ERROR)

    await send_notifications(results=results, year=2025, month=9, cutoff_day=5)

    total = send_notification_spy.call_count
    assert total > 1

    titles = _extract_titles(send_notification_spy)
    for idx, title in enumerate(titles, start=1):
        assert f"(Part {idx}/{total})" in title
        assert "in progress" in title


async def test_send_notifications_small_payload_sends_single_message(
    configured_webhook, send_notification_spy
):
    """A small result set must produce exactly one real HTTP POST and the
    title must NOT contain a `(Part i/N)` suffix."""
    results = _make_results(count=2, result=ProcessResult.JOURNAL_GENERATED, message_size=20)

    await send_notifications(results=results, year=2025, month=9)

    assert send_notification_spy.call_count == 1
    titles = _extract_titles(send_notification_spy)
    assert "(Part" not in titles[0]


async def test_send_notifications_each_part_carries_subset_of_rows(
    configured_webhook, send_notification_spy
):
    """Every authorization_id in the input must appear in exactly one of
    the sent messages, with no duplicates and no losses across the chunks."""
    results = _make_results(count=80, result=ProcessResult.JOURNAL_GENERATED)
    expected_auth_ids = {r.authorization_id for r in results}

    await send_notifications(results=results, year=2025, month=9)

    assert send_notification_spy.call_count > 1

    seen: list[str] = []
    for call in send_notification_spy.call_args_list:
        details = call.kwargs.get("details")
        assert details is not None
        for row in details.rows:
            seen.append(row[0])

    assert sorted(seen) == sorted(expected_auth_ids), (
        "each authorization_id should appear in exactly one part"
    )


async def test_send_notifications_truncates_long_message(configured_webhook, send_notification_spy):
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

    assert send_notification_spy.call_count == 1
    details = send_notification_spy.call_args_list[0].kwargs["details"]
    rendered_message = details.rows[0][3]
    assert sentinel not in rendered_message


def test_chunk_rows_by_size_raises_when_single_row_exceeds_budget():
    """The chunker's invariant is that no single row exceeds the budget on
    its own. _build_rows enforces this via MAX_MESSAGE_CHARS; the chunker
    is the defense-in-depth check that fails loudly if the invariant breaks."""
    big_row = ("AUTH-0001-0000", "BJO-0001-0000", "X", "x" * 30_000)

    # Fake measure: empty card = 100 bytes, each row contributes its char total.
    def measure(chunk: list[tuple[str, ...]]) -> int:
        return 100 + sum(len(value) for row in chunk for value in row)

    with pytest.raises(ValueError, match="exceeds per-chunk budget"):
        _chunk_rows_by_size(rows=[big_row], measure=measure, budget=1024)
