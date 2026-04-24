import calendar
import json
import logging
import textwrap
from collections.abc import Awaitable, Callable
from datetime import date

from adaptive_cards import card_types as ct  # type: ignore[import-untyped]

from app.billing.dataclasses import (
    ProcessResultInfo,
)
from app.billing.enum import NotificationLevel, ProcessResult
from app.notifications import (
    ColumnHeader,
    NotificationDetails,
    build_card_payload,
    send_exception,
    send_info,
    send_warning,
)

logger = logging.getLogger(__name__)
# MS Teams Incoming Webhook limit is 28 KB; we leave headroom for
# title/emoji/(Part i/N) prefixes and JSON whitespace not counted by our
# size estimator. See:
# https://learn.microsoft.com/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook
MSTEAMS_PAYLOAD_BUDGET = 22 * 1024
MAX_MESSAGE_CHARS = 2000

NOTIFICATION_TITLE_COLORS: dict[NotificationLevel, ct.Colors] = {
    NotificationLevel.SUCCESS: ct.Colors.ACCENT,
    NotificationLevel.IN_PROGRESS: ct.Colors.WARNING,
    NotificationLevel.ERROR: ct.Colors.ATTENTION,
}

NOTIFICATION_FUNCTIONS: dict[NotificationLevel, Callable[..., Awaitable[None]]] = {
    NotificationLevel.SUCCESS: send_info,
    NotificationLevel.IN_PROGRESS: send_warning,
    NotificationLevel.ERROR: send_exception,
}

NOTIFICATION_TEXTS: dict[NotificationLevel, tuple[str, str]] = {
    NotificationLevel.SUCCESS: (
        "{month_name} {year} Billing Finalized.",
        "Journals for the {month_name} {year} billing cycle have been successfully "
        "generated. The following journal objects were created:",
    ),
    NotificationLevel.IN_PROGRESS: (
        "Journals for the {month_name}-{year} billing cycle are in progress.",
        "Journals for the {month_name}-{year} billing cycle are in progress. Current status:",
    ),
    NotificationLevel.ERROR: (
        "The billing process for {month_name}-{year} was completed with Errors.",
        "The generation of some journals for the {month_name} {year} billing cycle failed:",
    ),
}

RESULT_ICON: dict[str, str] = {
    "JOURNAL_GENERATED": "✅",
    "JOURNAL_SKIPPED": "⏭️",
    "ERROR": "❌",
}


def _build_notification_title_text(
    level: NotificationLevel, month_name: str, year: int
) -> tuple[str, str]:
    title, text = NOTIFICATION_TEXTS[level]
    return (
        title.format(month_name=month_name, year=year),
        text.format(month_name=month_name, year=year),
    )


def _build_header() -> tuple[ColumnHeader, ...]:
    return (
        ColumnHeader(
            "Authorization", width="120px", horizontal_alignment=ct.HorizontalAlignment.CENTER
        ),
        ColumnHeader("Journal", width="120px", horizontal_alignment=ct.HorizontalAlignment.CENTER),
        ColumnHeader("Status", width="50px", horizontal_alignment=ct.HorizontalAlignment.CENTER),
        ColumnHeader("Message", width="stretch"),
    )


def _build_rows(details: list[ProcessResultInfo]) -> list[tuple[str, ...]]:
    return [
        (
            f"{item.authorization_id}",
            f"{item.journal_id or ''}",
            f"{RESULT_ICON.get(item.result.value.upper(), '')}",
            "\n\n".join(textwrap.wrap((item.message or "")[:MAX_MESSAGE_CHARS], width=80)),
        )
        for item in details
    ]


def _chunk_rows_by_size(
    rows: list[tuple[str, ...]],
    measure: Callable[[list[tuple[str, ...]]], int],
    budget: int = MSTEAMS_PAYLOAD_BUDGET,
) -> list[list[tuple[str, ...]]]:
    """
    Partition `rows` so each chunk's measured size stays within `budget`.
    `measure` returns the serialized size (bytes) of a card containing the
    given subset of rows, including all per-card overhead. Raises
    ``ValueError`` if a single row alone exceeds the budget — callers must
    cap the row's variable-size fields (the message column) at
    ``MAX_MESSAGE_CHARS`` in `_build_rows` so this invariant holds.
    """

    # json.dumps default separator between list items is ", " (2 bytes).
    separator_bytes = 2

    # Measure once: empty-card overhead.
    empty_size = measure([])
    # N measurements for marginal row sizes (each row in isolation).
    row_sizes = [measure([row]) - empty_size for row in rows]

    chunks: list[list[tuple[str, ...]]] = []
    buffer: list[tuple[str, ...]] = []
    buffer_size = empty_size

    for row, row_size in zip(rows, row_sizes, strict=True):
        added = row_size + (separator_bytes if buffer else 0)
        if buffer_size + added <= budget:
            buffer.append(row)
            buffer_size += added
            continue
        if buffer:
            chunks.append(buffer)
        if empty_size + row_size > budget:
            raise ValueError(
                f"Row for authorization={row[0]} contributes {row_size} bytes; "
                f"exceeds per-chunk budget {budget - empty_size}."
            )
        buffer = [row]
        buffer_size = empty_size + row_size
    if buffer:
        chunks.append(buffer)
    return chunks


def _measure_card_payload_size(
    title: str,
    text: str,
    header: tuple[ColumnHeader, ...],
    rows: list[tuple[str, ...]],
    title_color: ct.Colors = ct.Colors.DEFAULT,
    open_url: str | None = None,
) -> int:
    details = NotificationDetails(header=header, rows=rows)
    card_payload = build_card_payload(
        title=title,
        text=text,
        title_color=title_color,
        details=details,
        open_url=open_url,
    )
    return len(json.dumps(card_payload).encode("utf-8"))


async def _send_notification(
    level: NotificationLevel,
    month_name: str,
    year: int,
    results_counter_details: list[ProcessResultInfo],
) -> None:
    """
    Sends one or more notifications at the given level. Rows are split
    into multiple messages whenever the serialized payload would exceed
    `MSTEAMS_PAYLOAD_BUDGET`. Each part carries a "(Part i/N)" suffix
    in the title when N > 1.
    """

    func = NOTIFICATION_FUNCTIONS[level]
    title, text = _build_notification_title_text(level=level, month_name=month_name, year=year)
    header = _build_header()
    rows = _build_rows(details=results_counter_details)
    if not rows:
        await func(
            title=title,
            text=text,
            details=NotificationDetails(header=header, rows=[]),
        )
        return

    title_color = NOTIFICATION_TITLE_COLORS[level]

    def measure(chunk_rows: list[tuple[str, ...]]) -> int:
        return _measure_card_payload_size(
            title=title,
            text=text,
            header=header,
            rows=chunk_rows,
            title_color=title_color,
        )

    chunks = _chunk_rows_by_size(rows=rows, measure=measure)
    total = len(chunks)
    for idx, chunk_rows in enumerate(chunks, start=1):
        chunk_title = f"{title} (Part {idx}/{total})" if total > 1 else title
        await func(
            title=chunk_title,
            text=text,
            details=NotificationDetails(header=header, rows=chunk_rows),
        )


def check_results(
    results: list[ProcessResultInfo],
) -> tuple[bool, bool]:
    """
    This function process the given results list to calculate
    the number of journals successfully generated and the number of errors.
    """

    results_type = [item.result for item in results]
    return ProcessResult.JOURNAL_GENERATED in results_type, ProcessResult.ERROR in results_type


async def send_notifications(
    results: list[ProcessResultInfo], year: int, month: int, cutoff_day: int = 5
) -> None:
    """
    This function process the given results list and sends
    notifications according to the number of journals successfully generated
    and the number of errors.
    """
    logger.info(f"Processing billing results for {year}/{month} Cutoff day:{cutoff_day}")
    succeeded, failed = check_results(results)
    logger.info(f"Billing Process Success: {succeeded} - Failure:{failed}")
    month_name = calendar.month_name[month]
    today = date.today().day
    if succeeded and not failed:
        logger.info(f"Billing Process completed successfully for {month_name}-{year}.")
        await _send_notification(
            level=NotificationLevel.SUCCESS,
            month_name=month_name,
            year=year,
            results_counter_details=results,
        )

    elif failed:
        if today < cutoff_day:
            logger.warning(f"Journals for the {month_name}-{year} billing cycle are in progress.")
            await _send_notification(
                level=NotificationLevel.IN_PROGRESS,
                month_name=month_name,
                year=year,
                results_counter_details=results,
            )
        else:
            logger.error(f"The billing process for {month_name}-{year} was completed with Errors.")
            await _send_notification(
                level=NotificationLevel.ERROR,
                month_name=month_name,
                year=year,
                results_counter_details=results,
            )
