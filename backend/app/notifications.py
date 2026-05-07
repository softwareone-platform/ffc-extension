import asyncio
import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import httpx

from app.conf import get_settings

logger = logging.getLogger(__name__)

TITLE_PREFIX_INFO = "\U0001f44d"  # 👍
TITLE_PREFIX_WARNING = "⚠️"  # ⚠
TITLE_PREFIX_ERROR = "\U0001f4a3"  # 💣
TITLE_PREFIX_EXCEPTION = "\U0001f525"  # 🔥

_LIST_SEP = 1  # bytes for "," between sibling list items in compact JSON

# Reserve enough bytes in the title for the worst-case `(x of N)` suffix.
# `" (999 of 999)"` is 13 ASCII bytes; round up to 16 for a safety margin.
_PART_SUFFIX_RESERVED = 16

_TEXT_BLOCK_BASE = len(b'{"type":"TextBlock","text":}')
_TEXT_BLOCK_KEY_COLOR = len(b',"color":')
_TEXT_BLOCK_KEY_SIZE = len(b',"size":')
_TEXT_BLOCK_KEY_WEIGHT = len(b',"weight":')
_TEXT_BLOCK_KEY_WRAP_TRUE = len(b',"wrap":true')
_TEXT_BLOCK_KEY_HALIGN = len(b',"horizontalAlignment":')

_COLUMN_BASE = len(b'{"type":"Column","width":,"items":[]}')
_COLUMN_SET_HEADER_BASE = len(b'{"type":"ColumnSet","columns":[]}')
_COLUMN_SET_ROW_BASE = len(b'{"type":"ColumnSet","columns":[],"spacing":"small"}')
_CONTAINER_BASE = len(b'{"type":"Container","items":[]}')
_ACTION_OPEN_URL_BASE = len(b'{"type":"Action.OpenUrl","title":,"mode":"primary","url":}')
_ADAPTIVE_CARD_BASE = len(
    b'{"type":"AdaptiveCard","version":"1.4",'
    b'"$schema":"http://adaptivecards.io/schemas/adaptive-card.json",'
    b'"body":[],"actions":[],"msteams":{"width":"Full"}}'
)
_ENVELOPE_BASE = len(
    b'{"type":"message","attachments":'
    b'[{"contentType":"application/vnd.microsoft.card.adaptive","content":}]}'
)


# Maximum payload size, in bytes, accepted by the MS Teams Incoming/Workflow
# webhook. The cap is documented at 28 KB (28672 bytes) and applies to the
# entire JSON envelope (the `{"type":"message","attachments":[...]}` we POST,
# not just the inner adaptive card):
#
#   "The message size limit is 28 KB. When the size exceeds 28 KB, you receive
#    an error."
#   — https://learn.microsoft.com/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook
#
# When exceeded, MS Teams returns the error message
#   {"error":"The payload is too large. Please make sure the size is less than 28KB."}
# back through Power Automate (the HTTP trigger still returns 202 to us, so
# the rejection is visible only in the Power Automate run history).
#
# In practice payloads close to 28672 bytes are still rejected: chunks at
# 27.7 KB failed in production and the empirical safe upper bound was 26 KB.
# We pack chunks against this 26 KB target, leaving ~2 KB of headroom under
# the documented 28 KB cap.
MSTEAMS_PAYLOAD_LIMIT = 26 * 1024

# Power Automate request-throttling: 600 calls/min per connection,
# burst 100/10s. We pace at ≤ 4 req/s (~240/min) for a 6× margin.
MSTEAMS_MIN_INTERVAL_SECONDS = 0.25
MSTEAMS_MAX_RETRIES = 3
MSTEAMS_DEFAULT_RETRY_AFTER_SECONDS = 5
MSTEAMS_MAX_RETRY_AFTER_SECONDS = 60


class Color(StrEnum):
    DEFAULT = "default"
    ACCENT = "accent"
    WARNING = "warning"
    ATTENTION = "attention"
    DARK = "dark"


class FontSize(StrEnum):
    SMALL = "small"
    LARGE = "large"


class FontWeight(StrEnum):
    BOLDER = "bolder"


class HorizontalAlignment(StrEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class Spacing(StrEnum):
    SMALL = "small"


@dataclass
class ColumnHeader:
    text: str
    width: str = "auto"
    horizontal_alignment: HorizontalAlignment | None = None


class NotificationDetails:
    def __init__(self, header: tuple[str | ColumnHeader, ...], rows: list[tuple[str, ...]]):
        header_len = len(header)
        for i, row in enumerate(rows):
            if len(row) != header_len:
                raise ValueError(
                    f"Row {i} has {len(row)} columns; expected {header_len}. "
                    f"All rows must have the same number of columns as the header."
                )
        self.header = header
        self.rows = rows


def _header_text_and_width(col: str | ColumnHeader) -> tuple[str, str]:
    if isinstance(col, ColumnHeader):
        return col.text, col.width
    return str(col), "auto"


def _header_width(col: str | ColumnHeader) -> str:
    return col.width if isinstance(col, ColumnHeader) else "auto"


def _header_alignment(col: str | ColumnHeader) -> HorizontalAlignment | None:
    if isinstance(col, ColumnHeader):
        return col.horizontal_alignment
    return None


def _text_block(
    text: str,
    *,
    color: Color | None = None,
    size: FontSize | None = None,
    weight: FontWeight | None = None,
    wrap: bool | None = None,
    horizontal_alignment: HorizontalAlignment | None = None,
) -> dict[str, Any]:
    block: dict[str, Any] = {"type": "TextBlock", "text": text}
    if color is not None:
        block["color"] = color.value
    if size is not None:
        block["size"] = size.value
    if weight is not None:
        block["weight"] = weight.value
    if wrap is not None:
        block["wrap"] = wrap
    if horizontal_alignment is not None:
        block["horizontalAlignment"] = horizontal_alignment.value
    return block


def _column(width: str, items: list[dict]) -> dict[str, Any]:
    return {"type": "Column", "width": width, "items": items}


def _column_set(columns: list[dict], spacing: Spacing | None = None) -> dict[str, Any]:
    cs: dict[str, Any] = {"type": "ColumnSet", "columns": columns}
    if spacing is not None:
        cs["spacing"] = spacing.value
    return cs


def _container(items: list[dict]) -> dict[str, Any]:
    return {"type": "Container", "items": items}


def _action_open_url(title: str, url: str) -> dict[str, Any]:
    return {
        "type": "Action.OpenUrl",
        "title": title,
        "mode": "primary",
        "url": url,
    }


def _adaptive_card(body: list[dict], actions: list[dict]) -> dict[str, Any]:
    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "body": body,
        "actions": actions,
        "msteams": {"width": "Full"},
    }


def _envelope(card: dict) -> dict[str, Any]:
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card,
            }
        ],
    }


def _header_column_set(header: tuple[str | ColumnHeader, ...]) -> dict[str, Any]:
    columns: list[dict] = []
    for col_def in header:
        text, width = _header_text_and_width(col_def)
        alignment = _header_alignment(col_def)
        columns.append(
            _column(
                width=width,
                items=[
                    _text_block(
                        text,
                        color=Color.ACCENT,
                        weight=FontWeight.BOLDER,
                        wrap=True,
                        horizontal_alignment=alignment,
                    )
                ],
            )
        )
    return _column_set(columns)


def _row_column_set(
    header: tuple[str | ColumnHeader, ...],
    row: tuple[str, ...],
) -> dict[str, Any]:
    columns: list[dict] = []
    for col_def, value in zip(header, row, strict=True):
        width = _header_width(col_def)
        alignment = _header_alignment(col_def)
        columns.append(
            _column(
                width=width,
                items=[
                    _text_block(
                        value,
                        color=Color.DEFAULT,
                        wrap=True,
                        horizontal_alignment=alignment,
                    )
                ],
            )
        )
    return _column_set(columns, spacing=Spacing.SMALL)


def build_card_payload(
    *,
    title: str,
    text: str,
    title_color: Color,
    details: NotificationDetails | None = None,
    open_url: str | None = None,
) -> dict[str, Any]:
    body: list[dict] = [
        _text_block(
            title,
            size=FontSize.LARGE,
            weight=FontWeight.BOLDER,
            color=title_color,
        ),
        _text_block(
            text,
            size=FontSize.SMALL,
            color=Color.DEFAULT,
            wrap=True,
        ),
    ]
    if details is not None:
        container_items: list[dict] = [_header_column_set(details.header)]
        for row in details.rows:
            container_items.append(_row_column_set(details.header, row))
        body.append(_container(container_items))

    actions: list[dict] = []
    if open_url:
        actions.append(_action_open_url("Open", open_url))

    card = _adaptive_card(body=body, actions=actions)
    return _envelope(card)


def _json_string_bytes(s: str) -> int:
    """Compact-JSON byte size of `s` rendered as a JSON string literal,
    including the surrounding quotes. Matches json.dumps(s, ensure_ascii=False)."""
    n = 2  # the surrounding quotes
    for ch in s:
        cp = ord(ch)
        if cp == 0x22 or cp == 0x5C:  # '"' or '\\'
            n += 2
        elif cp in (0x08, 0x09, 0x0A, 0x0C, 0x0D):  # \b \t \n \f \r
            n += 2
        elif cp < 0x20:
            n += 6  # \uXXXX
        elif cp < 0x80:
            n += 1
        elif cp < 0x800:
            n += 2
        elif cp < 0x10000:
            n += 3
        else:
            n += 4
    return n


def _row_bytes(
    header: tuple[str | ColumnHeader, ...],
    row: tuple[str, ...],
) -> int:
    """Compact-JSON byte size of one data row's ColumnSet, computed structurally."""
    n = _COLUMN_SET_ROW_BASE
    for i, value in enumerate(row):
        col_def = header[i]
        width = _header_width(col_def)
        alignment = _header_alignment(col_def)

        tb_n = _TEXT_BLOCK_BASE + _json_string_bytes(value)
        tb_n += _TEXT_BLOCK_KEY_COLOR + _json_string_bytes(Color.DEFAULT.value)
        tb_n += _TEXT_BLOCK_KEY_WRAP_TRUE
        if alignment is not None:
            tb_n += _TEXT_BLOCK_KEY_HALIGN + _json_string_bytes(alignment.value)

        col_n = _COLUMN_BASE + _json_string_bytes(width) + tb_n
        n += col_n + (_LIST_SEP if i > 0 else 0)
    return n


def _empty_card_bytes(
    *,
    title: str,
    text: str,
    title_color: Color,
    header: tuple[str | ColumnHeader, ...],
    open_url: str | None,
) -> int:
    """Compact-JSON byte size of the card with NO data rows (just the header).
    Title size includes `_PART_SUFFIX_RESERVED` to cover the worst-case
    `(x of N)` suffix added when chunking."""

    title_n = _TEXT_BLOCK_BASE + _json_string_bytes(title) + _PART_SUFFIX_RESERVED
    title_n += _TEXT_BLOCK_KEY_COLOR + _json_string_bytes(title_color.value)
    title_n += _TEXT_BLOCK_KEY_SIZE + _json_string_bytes(FontSize.LARGE.value)
    title_n += _TEXT_BLOCK_KEY_WEIGHT + _json_string_bytes(FontWeight.BOLDER.value)

    text_n = _TEXT_BLOCK_BASE + _json_string_bytes(text)
    text_n += _TEXT_BLOCK_KEY_COLOR + _json_string_bytes(Color.DEFAULT.value)
    text_n += _TEXT_BLOCK_KEY_SIZE + _json_string_bytes(FontSize.SMALL.value)
    text_n += _TEXT_BLOCK_KEY_WRAP_TRUE

    header_col_set_n = _COLUMN_SET_HEADER_BASE
    for i, col_def in enumerate(header):
        text_val, width = _header_text_and_width(col_def)
        alignment = _header_alignment(col_def)

        tb_n = _TEXT_BLOCK_BASE + _json_string_bytes(text_val)
        tb_n += _TEXT_BLOCK_KEY_COLOR + _json_string_bytes(Color.ACCENT.value)
        tb_n += _TEXT_BLOCK_KEY_WEIGHT + _json_string_bytes(FontWeight.BOLDER.value)
        tb_n += _TEXT_BLOCK_KEY_WRAP_TRUE
        if alignment is not None:
            tb_n += _TEXT_BLOCK_KEY_HALIGN + _json_string_bytes(alignment.value)

        col_n = _COLUMN_BASE + _json_string_bytes(width) + tb_n
        header_col_set_n += col_n + (_LIST_SEP if i > 0 else 0)

    container_n = _CONTAINER_BASE + header_col_set_n

    # Body = [title, text, container] — 2 separators between 3 items.
    body_n = title_n + text_n + container_n + 2 * _LIST_SEP

    actions_n = 0
    if open_url is not None:
        actions_n = (
            _ACTION_OPEN_URL_BASE + _json_string_bytes("Open") + _json_string_bytes(open_url)
        )

    card_n = _ADAPTIVE_CARD_BASE + body_n + actions_n
    return _ENVELOPE_BASE + card_n


def _chunk_rows_by_size(
    rows: list[tuple[str, ...]],
    row_sizes: list[int],
    base_size: int,
) -> list[list[tuple[str, ...]]]:
    """Bin-pack rows so each chunk fits in MSTEAMS_PAYLOAD_LIMIT.

    Each row contributes `row_size + _LIST_SEP` bytes when added to a chunk
    because the data row is always preceded in `Container.items` by either
    the header ColumnSet or the previous data row, and compact JSON lists
    use a one-byte ``,`` separator. Raises ``ValueError`` if a single row
    alone would exceed the per-chunk capacity.
    """

    chunks: list[list[tuple[str, ...]]] = []
    buffer: list[tuple[str, ...]] = []
    buffer_size = base_size

    for row, row_size in zip(rows, row_sizes, strict=True):
        added = row_size + _LIST_SEP
        if buffer_size + added <= MSTEAMS_PAYLOAD_LIMIT:
            buffer.append(row)
            buffer_size += added
            continue
        if buffer:
            chunks.append(buffer)
        if base_size + _LIST_SEP + row_size > MSTEAMS_PAYLOAD_LIMIT:
            raise ValueError(
                f"Row for {row[0]!r} contributes {row_size} bytes; "
                f"exceeds per-chunk capacity "
                f"{MSTEAMS_PAYLOAD_LIMIT - base_size - _LIST_SEP}."
            )
        buffer = [row]
        buffer_size = base_size + _LIST_SEP + row_size

    if buffer:
        chunks.append(buffer)
    return chunks


def iter_card_messages(
    *,
    title: str,
    text: str,
    title_color: Color = Color.DEFAULT,
    details: NotificationDetails | None = None,
    open_url: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield one MS Teams message payload per chunk, each ≤ MSTEAMS_PAYLOAD_LIMIT
    bytes when serialized as compact JSON. When details is None or fits in a
    single message, yields exactly one payload (no `(x of N)` suffix). When
    chunking, each payload's title carries `(x of N)`."""

    if details is None or not details.rows:
        yield build_card_payload(
            title=title,
            text=text,
            title_color=title_color,
            details=details,
            open_url=open_url,
        )
        return

    base_size = _empty_card_bytes(
        title=title,
        text=text,
        title_color=title_color,
        header=details.header,
        open_url=open_url,
    )
    row_sizes = [_row_bytes(details.header, row) for row in details.rows]

    chunks = _chunk_rows_by_size(details.rows, row_sizes, base_size)
    total = len(chunks)
    for idx, chunk_rows in enumerate(chunks, start=1):
        chunk_title = f"{title} ({idx} of {total})" if total > 1 else title
        yield build_card_payload(
            title=chunk_title,
            text=text,
            title_color=title_color,
            details=NotificationDetails(header=details.header, rows=chunk_rows),
            open_url=open_url,
        )


def _retry_after_seconds(header: str | None) -> float:
    """Parse a Retry-After delta-seconds value. Falls back to the default on
    missing/malformed input; clamps to the per-attempt maximum."""
    if header is None:
        return MSTEAMS_DEFAULT_RETRY_AFTER_SECONDS
    try:
        value = float(header.strip())
    except ValueError:
        return MSTEAMS_DEFAULT_RETRY_AFTER_SECONDS
    if value < 0:
        return MSTEAMS_DEFAULT_RETRY_AFTER_SECONDS
    return min(value, float(MSTEAMS_MAX_RETRY_AFTER_SECONDS))


async def _post_with_retry(
    client: httpx.AsyncClient,
    *,
    url: str,
    body: bytes,
) -> None:
    """POST `body` to `url`, retrying on 429 / transient 5xx with Retry-After.
    Logs and returns on permanent failure rather than raising — preserves the
    log-and-continue contract of send_notification."""
    headers = {"Content-Type": "application/json"}
    for attempt in range(MSTEAMS_MAX_RETRIES + 1):
        response = await client.post(url, content=body, headers=headers)

        if response.status_code in (200, 202):
            return

        if response.status_code in (429, 502, 503, 504) and attempt < MSTEAMS_MAX_RETRIES:
            delay = _retry_after_seconds(response.headers.get("Retry-After"))
            logger.warning(
                "MSTeams throttled (status=%s, attempt=%d/%d); sleeping %.2fs before retry.",
                response.status_code,
                attempt + 1,
                MSTEAMS_MAX_RETRIES,
                delay,
            )
            await asyncio.sleep(delay)
            continue

        logger.error(
            f"Failed to send notification to MSTeams: {response.status_code} - {response.text}"
        )
        return


async def send_notification(
    title: str,
    text: str,
    title_color: Color = Color.DEFAULT,
    details: NotificationDetails | None = None,
    open_url: str | None = None,
) -> None:
    settings = get_settings()
    if not settings.msteams_notifications_webhook_url:  # pragma: no cover
        logger.warning("MSTeams notifications are disabled.")
        return

    async with httpx.AsyncClient() as client:
        first = True
        for message in iter_card_messages(
            title=title,
            text=text,
            title_color=title_color,
            details=details,
            open_url=open_url,
        ):
            if not first:
                await asyncio.sleep(MSTEAMS_MIN_INTERVAL_SECONDS)
            first = False

            body = json.dumps(message, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            await _post_with_retry(
                client,
                url=settings.msteams_notifications_webhook_url,
                body=body,
            )


async def send_info(
    title: str,
    text: str,
    details: NotificationDetails | None = None,
    open_url: str | None = None,
) -> None:
    await send_notification(
        f"{TITLE_PREFIX_INFO} {title}",
        text,
        title_color=Color.ACCENT,
        details=details,
        open_url=open_url,
    )


async def send_warning(
    title: str,
    text: str,
    details: NotificationDetails | None = None,
    open_url: str | None = None,
) -> None:
    await send_notification(
        f"{TITLE_PREFIX_WARNING} {title}",
        text,
        title_color=Color.WARNING,
        details=details,
        open_url=open_url,
    )


async def send_error(
    title: str,
    text: str,
    details: NotificationDetails | None = None,
    open_url: str | None = None,
) -> None:
    await send_notification(
        f"{TITLE_PREFIX_ERROR} {title}",
        text,
        title_color=Color.ATTENTION,
        details=details,
        open_url=open_url,
    )


async def send_exception(
    title: str,
    text: str,
    details: NotificationDetails | None = None,
    open_url: str | None = None,
) -> None:
    await send_notification(
        f"{TITLE_PREFIX_EXCEPTION} {title}",
        text,
        title_color=Color.ATTENTION,
        details=details,
        open_url=open_url,
    )
