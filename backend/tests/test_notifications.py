import json

import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from app.notifications import (
    _LIST_SEP,
    _PART_SUFFIX_RESERVED,
    MSTEAMS_DEFAULT_RETRY_AFTER_SECONDS,
    MSTEAMS_MAX_RETRIES,
    MSTEAMS_MAX_RETRY_AFTER_SECONDS,
    MSTEAMS_MIN_INTERVAL_SECONDS,
    MSTEAMS_PAYLOAD_LIMIT,
    Color,
    ColumnHeader,
    NotificationDetails,
    _chunk_rows_by_size,
    _empty_card_bytes,
    _json_string_bytes,
    _retry_after_seconds,
    _row_bytes,
    iter_card_messages,
    send_error,
    send_exception,
    send_info,
    send_notification,
    send_warning,
)


@pytest.mark.parametrize(
    ("function", "color", "icon"),
    [
        (send_info, Color.ACCENT, "\U0001f44d"),
        (send_warning, Color.WARNING, "⚠️"),
        (send_error, Color.ATTENTION, "\U0001f4a3"),
        (send_exception, Color.ATTENTION, "\U0001f525"),
    ],
)
async def test_send_others(mocker, function, color, icon):
    mocked_send_notification = mocker.patch(
        "app.notifications.send_notification",
    )

    await function("title", "text", details=None, open_url=None)

    mocked_send_notification.assert_awaited_once_with(
        f"{icon} title",
        "text",
        title_color=color,
        details=None,
        open_url=None,
    )


async def test_send_notification_full(httpx_mock: HTTPXMock, mocker: MockerFixture):
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
        match_json={
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "body": [
                            {
                                "text": "Title",
                                "type": "TextBlock",
                                "color": "dark",
                                "size": "large",
                                "weight": "bolder",
                            },
                            {
                                "text": "Text",
                                "type": "TextBlock",
                                "color": "default",
                                "size": "small",
                                "wrap": True,
                            },
                            {
                                "items": [
                                    {
                                        "type": "ColumnSet",
                                        "columns": [
                                            {
                                                "type": "Column",
                                                "items": [
                                                    {
                                                        "text": "Header 1",
                                                        "type": "TextBlock",
                                                        "color": "accent",
                                                        "weight": "bolder",
                                                        "wrap": True,
                                                    },
                                                ],
                                                "width": "auto",
                                            },
                                            {
                                                "type": "Column",
                                                "items": [
                                                    {
                                                        "text": "Header 2",
                                                        "type": "TextBlock",
                                                        "color": "accent",
                                                        "weight": "bolder",
                                                        "wrap": True,
                                                    },
                                                ],
                                                "width": "auto",
                                            },
                                        ],
                                    },
                                    {
                                        "spacing": "small",
                                        "type": "ColumnSet",
                                        "columns": [
                                            {
                                                "type": "Column",
                                                "items": [
                                                    {
                                                        "text": "Row 1 Col 1",
                                                        "type": "TextBlock",
                                                        "color": "default",
                                                        "wrap": True,
                                                    },
                                                ],
                                                "width": "auto",
                                            },
                                            {
                                                "type": "Column",
                                                "items": [
                                                    {
                                                        "text": "Row 1 Col 2",
                                                        "type": "TextBlock",
                                                        "color": "default",
                                                        "wrap": True,
                                                    },
                                                ],
                                                "width": "auto",
                                            },
                                        ],
                                    },
                                    {
                                        "spacing": "small",
                                        "type": "ColumnSet",
                                        "columns": [
                                            {
                                                "type": "Column",
                                                "items": [
                                                    {
                                                        "text": "Row 2 Col 1",
                                                        "type": "TextBlock",
                                                        "color": "default",
                                                        "wrap": True,
                                                    },
                                                ],
                                                "width": "auto",
                                            },
                                            {
                                                "type": "Column",
                                                "items": [
                                                    {
                                                        "text": "Row 2 Col 2",
                                                        "type": "TextBlock",
                                                        "color": "default",
                                                        "wrap": True,
                                                    },
                                                ],
                                                "width": "auto",
                                            },
                                        ],
                                    },
                                ],
                                "type": "Container",
                            },
                        ],
                        "actions": [
                            {
                                "title": "Open",
                                "mode": "primary",
                                "url": "https://example.com",
                                "type": "Action.OpenUrl",
                            },
                        ],
                        "msteams": {"width": "Full"},
                    },
                }
            ],
        },
    )

    await send_notification(
        "Title",
        "Text",
        title_color=Color.DARK,
        open_url="https://example.com",
        details=NotificationDetails(
            header=("Header 1", "Header 2"),
            rows=[("Row 1 Col 1", "Row 1 Col 2"), ("Row 2 Col 1", "Row 2 Col 2")],
        ),
    )


async def test_send_notification_simple(httpx_mock: HTTPXMock, mocker: MockerFixture):
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
        match_json={
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "body": [
                            {
                                "text": "Title",
                                "type": "TextBlock",
                                "color": "dark",
                                "size": "large",
                                "weight": "bolder",
                            },
                            {
                                "text": "Text",
                                "type": "TextBlock",
                                "color": "default",
                                "size": "small",
                                "wrap": True,
                            },
                        ],
                        "actions": [],
                        "msteams": {"width": "Full"},
                    },
                }
            ],
        },
    )

    await send_notification(
        "Title",
        "Text",
        title_color=Color.DARK,
    )


async def test_send_notification_error(
    caplog: pytest.LogCaptureFixture,
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
):
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=500,
        content=b"Internal Server Error",
    )

    with caplog.at_level("ERROR"):
        await send_notification(
            "Title",
            "Text",
            title_color=Color.DARK,
        )
    assert ("Failed to send notification to MSTeams: 500 - Internal Server Error") in caplog.text


# ---------------------------------------------------------------------------
# Structural string sizer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "",
        "plain ascii",
        'has "quotes"',
        "has \\ backslash",
        "tab\there",
        "nl\nthere",
        "control\x01\x1f",
        "café",  # multi-byte
        "日本語",  # 3-byte
        "𝟘𝟙",  # 4-byte
        " (1 of 2)",
        "(999 of 999)",
    ],
)
def test_json_string_bytes_matches_compact_dumps(value: str) -> None:
    expected = len(json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    assert _json_string_bytes(value) == expected


# ---------------------------------------------------------------------------
# iter_card_messages
# ---------------------------------------------------------------------------


def _short_details() -> NotificationDetails:
    return NotificationDetails(
        header=("A", "B"),
        rows=[("a1", "b1"), ("a2", "b2")],
    )


def _wide_details(count: int = 80, message_size: int = 600) -> NotificationDetails:
    long_msg = "x" * message_size
    return NotificationDetails(
        header=(
            ColumnHeader("Authorization", width="120px"),
            ColumnHeader("Journal", width="120px"),
            ColumnHeader("Status", width="50px"),
            ColumnHeader("Message", width="stretch"),
        ),
        rows=[
            (
                f"AUTH-{i:04d}-0000",
                f"BJO-{i:04d}-0000",
                "✅",
                f"{long_msg} idx={i}",
            )
            for i in range(count)
        ],
    )


def test_iter_card_messages_no_details() -> None:
    messages = list(iter_card_messages(title="T", text="x"))
    assert len(messages) == 1
    body = messages[0]["attachments"][0]["content"]["body"]
    assert body[0]["text"] == "T"
    assert "(" not in body[0]["text"]


def test_iter_card_messages_empty_rows() -> None:
    details = NotificationDetails(header=("A",), rows=[])
    messages = list(iter_card_messages(title="T", text="x", details=details))
    assert len(messages) == 1
    body = messages[0]["attachments"][0]["content"]["body"]
    assert body[0]["text"] == "T"


def test_iter_card_messages_single_chunk() -> None:
    messages = list(iter_card_messages(title="T", text="x", details=_short_details()))
    assert len(messages) == 1
    body = messages[0]["attachments"][0]["content"]["body"]
    assert body[0]["text"] == "T"  # no `(x of N)` suffix


def test_iter_card_messages_chunks_under_limit() -> None:
    messages = list(iter_card_messages(title="T", text="x", details=_wide_details()))
    assert len(messages) > 1
    for msg in messages:
        size = len(json.dumps(msg, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
        assert size <= MSTEAMS_PAYLOAD_LIMIT


def test_iter_card_messages_chunked_titles_carry_x_of_n() -> None:
    messages = list(iter_card_messages(title="My Title", text="x", details=_wide_details()))
    total = len(messages)
    assert total > 1
    for idx, msg in enumerate(messages, start=1):
        title = msg["attachments"][0]["content"]["body"][0]["text"]
        assert title == f"My Title ({idx} of {total})"


def test_iter_card_messages_oversized_single_row_raises() -> None:
    huge = "x" * (MSTEAMS_PAYLOAD_LIMIT + 100)
    details = NotificationDetails(header=("A",), rows=[(huge,)])
    with pytest.raises(ValueError, match="exceeds per-chunk capacity"):
        list(iter_card_messages(title="T", text="x", details=details))


def test_iter_card_messages_measurement_is_tight() -> None:
    """Predicted = base + Σrows + R*_LIST_SEP. Must be ≥ actual compact-JSON bytes,
    and within _PART_SUFFIX_RESERVED (the title-suffix headroom)."""
    details = _wide_details(count=40, message_size=200)
    title = "Test"
    text = "Body"

    base_size = _empty_card_bytes(
        title=title,
        text=text,
        title_color=Color.DEFAULT,
        header=details.header,
        open_url=None,
    )
    row_sizes = [_row_bytes(details.header, row) for row in details.rows]

    messages = list(
        iter_card_messages(title=title, text=text, details=details, title_color=Color.DEFAULT)
    )
    chunks = _chunk_rows_by_size(details.rows, row_sizes, base_size)
    assert len(chunks) == len(messages)

    row_to_size = dict(zip(details.rows, row_sizes, strict=True))
    for chunk_rows, msg in zip(chunks, messages, strict=True):
        predicted = (
            base_size + sum(row_to_size[row] for row in chunk_rows) + _LIST_SEP * len(chunk_rows)
        )
        actual = len(json.dumps(msg, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
        assert predicted >= actual
        assert predicted - actual <= _PART_SUFFIX_RESERVED


def test_iter_card_messages_no_json_dumps_during_measurement(mocker: MockerFixture) -> None:
    """Row sizing must be purely structural: no json.dumps may run during it.
    The only json.dumps allowed is one per yielded chunk inside build_card_payload?
    Actually build_card_payload returns a dict — json.dumps happens in send_notification.
    iter_card_messages itself must not call json.dumps at all."""
    spy = mocker.spy(json, "dumps")

    list(iter_card_messages(title="T", text="x", details=_wide_details()))

    assert spy.call_count == 0


# ---------------------------------------------------------------------------
# _chunk_rows_by_size unit
# ---------------------------------------------------------------------------


def test_chunk_rows_by_size_raises_when_single_row_exceeds_capacity() -> None:
    rows = [("AUTH",)]
    row_sizes = [MSTEAMS_PAYLOAD_LIMIT + 100]
    with pytest.raises(ValueError, match="exceeds per-chunk capacity"):
        _chunk_rows_by_size(rows, row_sizes, base_size=100)


def test_chunk_rows_by_size_single_chunk_when_all_fit() -> None:
    rows = [("a",), ("b",), ("c",)]
    row_sizes = [10, 10, 10]
    chunks = _chunk_rows_by_size(rows, row_sizes, base_size=100)
    assert chunks == [rows]


def test_chunk_rows_by_size_splits_by_capacity() -> None:
    rows = [("a",), ("b",), ("c",), ("d",)]
    row_sizes = [10_000, 10_000, 10_000, 10_000]
    chunks = _chunk_rows_by_size(rows, row_sizes, base_size=1000)
    assert len(chunks) > 1
    assert [r for chunk in chunks for r in chunk] == rows


# ---------------------------------------------------------------------------
# Wire format: compact JSON
# ---------------------------------------------------------------------------


async def test_send_notification_writes_compact_json(
    httpx_mock: HTTPXMock, mocker: MockerFixture
) -> None:
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
    )

    await send_notification("Title", "Text", title_color=Color.DARK)

    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    raw = requests[0].content
    # Compact JSON has no whitespace separators.
    assert b", " not in raw
    assert b": " not in raw
    # Must still be valid JSON.
    parsed = json.loads(raw)
    assert parsed["type"] == "message"


async def test_send_notification_splits_when_oversized(
    httpx_mock: HTTPXMock, mocker: MockerFixture
) -> None:
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    # Skip pacing in the test
    mocker.patch("app.notifications.asyncio.sleep", new_callable=mocker.AsyncMock)
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
        is_reusable=True,
    )

    await send_notification("Title", "Text", details=_wide_details())

    requests = httpx_mock.get_requests()
    assert len(requests) > 1
    total = len(requests)
    for idx, request in enumerate(requests, start=1):
        assert len(request.content) <= MSTEAMS_PAYLOAD_LIMIT
        parsed = json.loads(request.content)
        title = parsed["attachments"][0]["content"]["body"][0]["text"]
        assert title == f"Title ({idx} of {total})"


# ---------------------------------------------------------------------------
# Pacing
# ---------------------------------------------------------------------------


async def test_send_notification_does_not_pace_single_message(
    httpx_mock: HTTPXMock, mocker: MockerFixture
) -> None:
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    sleep_mock = mocker.patch("app.notifications.asyncio.sleep", new_callable=mocker.AsyncMock)
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
    )

    await send_notification("Title", "Text")

    sleep_mock.assert_not_called()


async def test_send_notification_paces_between_chunks(
    httpx_mock: HTTPXMock, mocker: MockerFixture
) -> None:
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    sleep_mock = mocker.patch("app.notifications.asyncio.sleep", new_callable=mocker.AsyncMock)
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
        is_reusable=True,
    )

    await send_notification("Title", "Text", details=_wide_details())

    requests = httpx_mock.get_requests()
    n = len(requests)
    assert n > 1
    pacing_calls = [
        c for c in sleep_mock.await_args_list if c.args == (MSTEAMS_MIN_INTERVAL_SECONDS,)
    ]
    assert len(pacing_calls) == n - 1


# ---------------------------------------------------------------------------
# Retry-After parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("header_value", "expected"),
    [
        (None, MSTEAMS_DEFAULT_RETRY_AFTER_SECONDS),
        ("3", 3.0),
        ("0", 0.0),
        ("-5", MSTEAMS_DEFAULT_RETRY_AFTER_SECONDS),
        ("not a number", MSTEAMS_DEFAULT_RETRY_AFTER_SECONDS),
        ("3600", float(MSTEAMS_MAX_RETRY_AFTER_SECONDS)),  # clamped
        ("  4 ", 4.0),
    ],
)
def test_retry_after_seconds(header_value: str | None, expected: float) -> None:
    assert _retry_after_seconds(header_value) == expected


# ---------------------------------------------------------------------------
# Retry behavior
# ---------------------------------------------------------------------------


async def test_send_notification_retries_on_429(
    httpx_mock: HTTPXMock, mocker: MockerFixture
) -> None:
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    sleep_mock = mocker.patch("app.notifications.asyncio.sleep", new_callable=mocker.AsyncMock)

    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=429,
        headers={"Retry-After": "3"},
    )
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
    )

    await send_notification("Title", "Text")

    assert len(httpx_mock.get_requests()) == 2
    assert sleep_mock.await_args_list == [mocker.call(3.0)]


async def test_send_notification_retries_on_transient_5xx(
    httpx_mock: HTTPXMock, mocker: MockerFixture
) -> None:
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    sleep_mock = mocker.patch("app.notifications.asyncio.sleep", new_callable=mocker.AsyncMock)

    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=503,
    )
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
    )

    await send_notification("Title", "Text")

    assert len(httpx_mock.get_requests()) == 2
    sleep_mock.assert_awaited_once_with(MSTEAMS_DEFAULT_RETRY_AFTER_SECONDS)


async def test_send_notification_honors_retry_after_cap(
    httpx_mock: HTTPXMock, mocker: MockerFixture
) -> None:
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    sleep_mock = mocker.patch("app.notifications.asyncio.sleep", new_callable=mocker.AsyncMock)

    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=429,
        headers={"Retry-After": "3600"},
    )
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
    )

    await send_notification("Title", "Text")

    sleep_mock.assert_awaited_once_with(float(MSTEAMS_MAX_RETRY_AFTER_SECONDS))


async def test_send_notification_retry_after_missing_uses_default(
    httpx_mock: HTTPXMock, mocker: MockerFixture
) -> None:
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    sleep_mock = mocker.patch("app.notifications.asyncio.sleep", new_callable=mocker.AsyncMock)

    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=429,
    )
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
    )

    await send_notification("Title", "Text")

    sleep_mock.assert_awaited_once_with(MSTEAMS_DEFAULT_RETRY_AFTER_SECONDS)


async def test_send_notification_retry_after_malformed_uses_default(
    httpx_mock: HTTPXMock, mocker: MockerFixture
) -> None:
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    sleep_mock = mocker.patch("app.notifications.asyncio.sleep", new_callable=mocker.AsyncMock)

    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=429,
        headers={"Retry-After": "tomorrow"},
    )
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
    )

    await send_notification("Title", "Text")

    sleep_mock.assert_awaited_once_with(MSTEAMS_DEFAULT_RETRY_AFTER_SECONDS)


async def test_send_notification_gives_up_after_max_retries(
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    mocker.patch("app.notifications.asyncio.sleep", new_callable=mocker.AsyncMock)

    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=429,
        headers={"Retry-After": "1"},
        is_reusable=True,
    )

    with caplog.at_level("ERROR"):
        await send_notification("Title", "Text")

    assert len(httpx_mock.get_requests()) == MSTEAMS_MAX_RETRIES + 1
    assert "Failed to send notification to MSTeams: 429" in caplog.text


async def test_send_notification_does_not_retry_on_4xx(
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    sleep_mock = mocker.patch("app.notifications.asyncio.sleep", new_callable=mocker.AsyncMock)
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=400,
        content=b"Bad Request",
    )

    with caplog.at_level("ERROR"):
        await send_notification("Title", "Text")

    assert len(httpx_mock.get_requests()) == 1
    sleep_mock.assert_not_called()
    assert "Failed to send notification to MSTeams: 400 - Bad Request" in caplog.text


async def test_send_notification_retry_inside_multi_chunk(
    httpx_mock: HTTPXMock, mocker: MockerFixture
) -> None:
    """3-chunk send. Chunk #2's first attempt 429s with Retry-After: 7, then 202.
    Total POSTs = 4. Sleep calls = 3 (2 inter-chunk pacing + 1 retry).
    Order: POST(1) → sleep(0.25) → POST(2 attempt 1, 429) → sleep(7.0)
           → POST(2 attempt 2, 202) → sleep(0.25) → POST(3)."""
    mocked_settings = mocker.MagicMock()
    mocked_settings.msteams_notifications_webhook_url = "https://example.com"
    mocker.patch("app.notifications.get_settings", return_value=mocked_settings)
    sleep_mock = mocker.patch("app.notifications.asyncio.sleep", new_callable=mocker.AsyncMock)

    # Build a details payload that produces exactly 3 chunks.
    details = _wide_details(count=50, message_size=600)
    pre_messages = list(iter_card_messages(title="T", text="x", details=details))
    assert len(pre_messages) == 3, f"test setup expects 3 chunks, got {len(pre_messages)}"

    # Responses: 202, 429, 202, 202 in order.
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
    )
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=429,
        headers={"Retry-After": "7"},
    )
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
    )
    httpx_mock.add_response(
        method="POST",
        url=mocked_settings.msteams_notifications_webhook_url,
        status_code=202,
    )

    await send_notification("T", "x", details=details)

    assert len(httpx_mock.get_requests()) == 4
    delays = [c.args[0] for c in sleep_mock.await_args_list]
    assert delays == [MSTEAMS_MIN_INTERVAL_SECONDS, 7.0, MSTEAMS_MIN_INTERVAL_SECONDS]
