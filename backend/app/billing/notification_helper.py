import calendar
import logging
import textwrap
from collections.abc import Awaitable, Callable
from datetime import date

from app.billing.dataclasses import (
    ProcessResultInfo,
)
from app.billing.enum import NotificationLevel, ProcessResult
from app.notifications import (
    ColumnHeader,
    HorizontalAlignment,
    NotificationDetails,
    send_exception,
    send_info,
    send_warning,
)

logger = logging.getLogger(__name__)

MAX_MESSAGE_CHARS = 2000

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
            "Authorization", width="120px", horizontal_alignment=HorizontalAlignment.CENTER
        ),
        ColumnHeader("Journal", width="120px", horizontal_alignment=HorizontalAlignment.CENTER),
        ColumnHeader("Status", width="50px", horizontal_alignment=HorizontalAlignment.CENTER),
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


async def _send_notification(
    level: NotificationLevel,
    month_name: str,
    year: int,
    results_counter_details: list[ProcessResultInfo],
) -> None:
    func = NOTIFICATION_FUNCTIONS[level]
    title, text = _build_notification_title_text(level=level, month_name=month_name, year=year)
    header = _build_header()
    rows = _build_rows(details=results_counter_details)
    await func(
        title=title,
        text=text,
        details=NotificationDetails(header=header, rows=rows),
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
