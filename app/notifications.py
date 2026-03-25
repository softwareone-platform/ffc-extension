import logging
from dataclasses import dataclass

import httpx
from adaptive_cards import card_types as ct
from adaptive_cards.actions import ActionOpenUrl
from adaptive_cards.card import AdaptiveCard
from adaptive_cards.card_types import MSTeams, MSTeamsCardWidth
from adaptive_cards.containers import Column, ColumnSet, Container
from adaptive_cards.elements import TextBlock

from app.conf import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ColumnHeader:
    text: str
    width: str = "auto"
    horizontal_alignment: ct.HorizontalAlignment | None = None


class NotificationDetails:
    def __init__(self, header: tuple[str | ColumnHeader, ...], rows: list[tuple[str, ...]]):
        if not all(len(t) == len(header) for t in rows):
            raise ValueError("All rows must have the same number of columns as the header.")
        self.header = header
        self.rows = rows

    @staticmethod
    def _get_header_text_and_width(col: str | ColumnHeader) -> tuple[str, str]:
        if isinstance(col, ColumnHeader):
            return col.text, col.width
        return str(col), "auto"

    def to_container(self) -> Container:
        items = []

        # Header row
        header_columns = []
        for col in self.header:
            text, width = self._get_header_text_and_width(col)
            alignment = (
                col.horizontal_alignment.value
                if isinstance(col, ColumnHeader) and col.horizontal_alignment
                else None
            )
            header_columns.append(
                Column(
                    width=width,
                    items=[
                        TextBlock(
                            text=text,
                            horizontal_alignment=alignment,
                            weight=ct.FontWeight.BOLDER,
                            wrap=True,
                            color=ct.Colors.ACCENT,
                        )
                    ],
                )
            )
        items.append(ColumnSet(columns=header_columns))

        # Data rows
        for _idx, row in enumerate(self.rows):
            row_columns = []
            for col_idx, value in enumerate(row):
                col = self.header[col_idx]
                _, width = self._get_header_text_and_width(col)
                alignment = (
                    col.horizontal_alignment.value
                    if isinstance(col, ColumnHeader) and col.horizontal_alignment
                    else None
                )
                row_columns.append(
                    Column(
                        width=width,
                        items=[
                            TextBlock(
                                text=value,
                                horizontal_alignment=alignment,
                                wrap=True,
                                color=ct.Colors.DEFAULT,
                            )
                        ],
                    )
                )
            items.append(
                ColumnSet(
                    columns=row_columns,
                    spacing=ct.Spacing.SMALL,
                )
            )

        return Container(items=items)


async def send_notification(
    title: str,
    text: str,
    title_color: ct.Colors = ct.Colors.DEFAULT,
    details: NotificationDetails | None = None,
    open_url: str | None = None,
) -> None:
    settings = get_settings()
    if not settings.msteams_notifications_webhook_url:  # pragma: no cover
        logger.warning("MSTeams notifications are disabled.")
        return

    card_items = [
        TextBlock(
            text=title,
            size=ct.FontSize.LARGE,
            weight=ct.FontWeight.BOLDER,
            color=title_color,
        ),
        TextBlock(
            text=text,
            wrap=True,
            size=ct.FontSize.SMALL,
            color=ct.Colors.DEFAULT,
        ),
    ]
    if details:
        card_items.append(details.to_container())

    card_actions = []
    if open_url:
        card_actions.append(ActionOpenUrl(title="Open", url=open_url))

    card = (
        AdaptiveCard.new().version("1.4").add_items(card_items).add_actions(card_actions).create()
    )

    card.msteams = MSTeams(width=MSTeamsCardWidth.FULL)
    message = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card.to_dict(),
            },
        ],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            settings.msteams_notifications_webhook_url,
            json=message,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 202:
            logger.error(
                f"Failed to send notification to MSTeams: {response.status_code} - {response.text}"
            )


async def send_info(
    title: str,
    text: str,
    details: NotificationDetails | None = None,
    open_url: str | None = None,
) -> None:
    await send_notification(
        f"\U0001f44d {title}",
        text,
        title_color=ct.Colors.ACCENT,
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
        f"\u2622 {title}",
        text,
        title_color=ct.Colors.WARNING,
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
        f"\U0001f4a3 {title}",
        text,
        title_color=ct.Colors.ATTENTION,
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
        f"\U0001f525 {title}",
        text,
        title_color=ct.Colors.ATTENTION,
        details=details,
        open_url=open_url,
    )
