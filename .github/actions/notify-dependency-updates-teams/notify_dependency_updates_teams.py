#!/usr/bin/env python3
"""Post a dependency updates report to Microsoft Teams.

The card mirrors the layout of notify-pr-teams-action and of the Sonar quality
gate card so that the notifications read as a set. One card is sent per report,
so backend, frontend and e2e always arrive separately, and security fixes apart
from minor and patch updates.
"""

import json
import os
from typing import Any

import requests

# Teams rejects cards above ~28 KB, so long reports are cut and point to the PR.
MAX_CARD_BYTES = 27_000
MAX_ROWS = 20
MAX_VULNERABILITIES_PER_ROW = 3
MAX_SUMMARY_LENGTH = 120

SEVERITY_ORDER = ("critical", "high", "medium", "low")


def text_block(text: str, **extra: Any) -> dict[str, Any]:
    return {"type": "TextBlock", "text": text, "wrap": True, **extra}


def subtle_block(text: str) -> dict[str, Any]:
    return text_block(text, isSubtle=True, size="Small", spacing="None")


def truncate(text: str, length: int) -> str:
    return text if len(text) <= length else f"{text[: length - 1].rstrip()}…"


def get_severity_badge(rows: list[dict[str, Any]]) -> tuple[str, str]:
    """Badge text and style from the most severe vulnerability in the report."""
    severities = [v["severity"].lower() for row in rows for v in row["vulnerabilities"]]
    worst = next((s for s in SEVERITY_ORDER if s in severities), "unknown")
    style = {"critical": "Attention", "high": "Attention", "medium": "Warning"}.get(
        worst, "Accent"
    )
    return worst.capitalize(), style


def vulnerability_items(row: dict[str, Any]) -> list[dict[str, Any]]:
    vulnerabilities = row["vulnerabilities"]
    items = []
    for v in vulnerabilities[:MAX_VULNERABILITIES_PER_ROW]:
        cve = f" · {v['cve_id']}" if v.get("cve_id") else ""
        items.append(
            text_block(
                f"[{v['id']}]({v['advisory_url']}){cve} · "
                f"**{v['severity'].capitalize()}**",
                spacing="None",
            )
        )
        if v.get("summary"):
            items.append(subtle_block(truncate(v["summary"], MAX_SUMMARY_LENGTH)))
    hidden = len(vulnerabilities) - MAX_VULNERABILITIES_PER_ROW
    if hidden > 0:
        items.append(subtle_block(f"+{hidden} more"))
    return items


def table(
    titles: list[str], rows: list[list[list[dict[str, Any]]]], widths: list[int]
) -> dict[str, Any]:
    """A table whose cells are lists of card elements, under a header row."""
    header = {
        "type": "TableRow",
        "style": "accent",
        "cells": [
            {"type": "TableCell", "items": [text_block(f"**{title}**")]}
            for title in titles
        ],
    }
    return {
        "type": "Table",
        "gridStyle": "accent",
        "firstRowAsHeaders": True,
        "showGridLines": True,
        "verticalCellContentAlignment": "Top",
        "columns": [{"width": width} for width in widths],
        "rows": [
            header,
            *(
                {
                    "type": "TableRow",
                    "cells": [{"type": "TableCell", "items": cell} for cell in row],
                }
                for row in rows
            ),
        ],
    }


def more_rows(hidden: int) -> list[dict[str, Any]]:
    if hidden <= 0:
        return []
    return [
        text_block(
            f"…and {hidden} more, listed in the workflow run summary.",
            isSubtle=True,
            spacing="Small",
        )
    ]


def security_table(
    rows: list[dict[str, Any]], manual: bool, max_rows: int
) -> list[dict[str, Any]]:
    """One table row per package: affected, fixed and vulnerability columns."""
    cells = []
    for row in rows[:max_rows]:
        package = [text_block(f"**{row['package']}**")]
        if manual and row.get("reason"):
            package.append(subtle_block(truncate(row["reason"], MAX_SUMMARY_LENGTH)))
        if manual:
            fixed = ", ".join(row["patched_versions"]) or "n/a"
        else:
            fixed = ", ".join(row["fixed_versions"]) or "removed"
        cells.append(
            [
                package,
                [text_block(", ".join(row["affected_versions"]))],
                [text_block(fixed)],
                vulnerability_items(row),
            ]
        )
    titles = [
        "Dependency",
        "Affected version",
        "Patched in" if manual else "Fixed version",
        "Vulnerability",
    ]
    return [table(titles, cells, [2, 1, 1, 3]), *more_rows(len(rows) - max_rows)]


def security_sections(report: dict[str, Any], max_rows: int) -> list[dict[str, Any]]:
    fixed = report["fixed"]
    manual = report["manual"]
    vulnerability_count = sum(len(row["vulnerabilities"]) for row in fixed)
    body = [
        text_block(
            f"**Base branch:** {report['base']} · "
            f"**Dependencies to update:** {len(fixed)} · "
            f"**Vulnerabilities fixed:** {vulnerability_count} · "
            f"**Needs manual action:** {len(manual)}",
            spacing="Small",
        ),
        text_block("**Dependencies to update**", size="Large", spacing="Medium"),
        *security_table(fixed, manual=False, max_rows=max_rows),
    ]
    if manual:
        body += [
            text_block("**Needs manual action**", size="Large", spacing="Medium"),
            text_block(
                "These vulnerabilities could not be fixed from the lockfile alone.",
                isSubtle=True,
                spacing="None",
            ),
            *security_table(manual, manual=True, max_rows=max_rows),
        ]
    return body


def version_sections(report: dict[str, Any], max_rows: int) -> list[dict[str, Any]]:
    updates = report["updates"]
    direct = [u for u in updates if u["direct"]]
    transitive = [u for u in updates if not u["direct"]]
    # Direct dependencies are what reviewers act on; transitive ones only show
    # when nothing direct moved.
    shown = direct or transitive
    cells = [
        [
            [text_block(f"**{u['package']}**")],
            [text_block(", ".join(u["from_versions"]))],
            [text_block(", ".join(u["to_versions"]))],
            [text_block(u["update_type"].capitalize())],
        ]
        for u in shown[:max_rows]
    ]
    return [
        text_block(
            f"**Base branch:** {report['base']} · "
            f"**Direct dependencies:** {len(direct)} · "
            f"**Transitive dependencies:** {len(transitive)}",
            spacing="Small",
        ),
        text_block(
            "**Direct dependencies to update**"
            if direct
            else "**Transitive dependencies to update**",
            size="Large",
            spacing="Medium",
        ),
        table(
            ["Dependency", "Current version", "New version", "Update"],
            cells,
            [3, 2, 2, 1],
        ),
        *more_rows(len(shown) - max_rows),
        *internal_note(report.get("internal", {})),
    ]


def internal_note(internal: dict[str, str]) -> list[dict[str, Any]]:
    if not internal:
        return []
    held = ", ".join(f"{name} {version}" for name, version in internal.items())
    return [
        text_block(
            f"**Held at their current version (bump by hand):** {held}",
            isSubtle=True,
            spacing="Medium",
        )
    ]


def create_adaptive_card(
    bot_image_url: str,
    report: dict[str, Any],
    title: str,
    run_url: str,
    max_rows: int = MAX_ROWS,
) -> dict[str, Any]:
    """Create the adaptive card JSON payload."""
    label = report["label"]
    if report["kind"] == "security":
        heading = f"Security updates — {label}"
        badge_text, badge_style = get_severity_badge(report["fixed"] + report["manual"])
        sections = security_sections(report, max_rows)
    else:
        heading = f"Minor and patch updates — {label}"
        badge_text, badge_style = f"{len(report['updates'])} updates", "Accent"
        sections = version_sections(report, max_rows)

    body: list[dict[str, Any]] = [
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "Image",
                            "url": bot_image_url,
                            "size": "Medium",
                            "style": "RoundedCorners",
                        }
                    ],
                },
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        text_block(f"**{heading}**"),
                        text_block(f"**{report['repo']}**", color="Good"),
                    ],
                },
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "Badge",
                            "text": badge_text,
                            "size": "Large",
                            "style": badge_style,
                            "shape": "Rounded",
                            "appearance": "Tint",
                        }
                    ],
                },
            ],
        },
        text_block(
            title,
            size="ExtraLarge",
            weight="Bolder",
            color="Accent",
        ),
        *sections,
    ]

    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
                    "speak": heading,
                    "type": "AdaptiveCard",
                    "version": "1.5",
                    "body": body,
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "View workflow run",
                            "url": run_url,
                        },
                    ],
                    "msteams": {"width": "full"},
                },
            }
        ],
    }


def main():
    # Get environment variables
    webhook_url = os.environ["WEBHOOK_URL"]
    bot_image_url = os.environ["BOT_IMAGE_URL"]
    report_file = os.environ["REPORT_FILE"]
    title = os.environ["TITLE"]
    run_url = os.environ["RUN_URL"]

    with open(report_file, encoding="utf-8") as file:
        report = json.load(file)

    # Create payload, dropping table rows until Teams accepts its size
    for max_rows in range(MAX_ROWS, 0, -1):
        payload = create_adaptive_card(
            bot_image_url=bot_image_url,
            report=report,
            title=title,
            run_url=run_url,
            max_rows=max_rows,
        )
        if len(json.dumps(payload).encode()) <= MAX_CARD_BYTES:
            break

    # Print payload for debugging
    print(json.dumps(payload, indent=2))

    # Send to Teams
    response = requests.post(
        webhook_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    response.raise_for_status()


if __name__ == "__main__":
    main()
