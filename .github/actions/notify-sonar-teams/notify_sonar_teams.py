#!/usr/bin/env python3
"""Post a SonarQube Cloud Quality Gate result to Microsoft Teams.

The card mirrors the layout of notify-pr-teams-action so that the quality gate
notification and the pull request notification read as a set.
"""

import json
import os
from typing import Any

import requests

METRIC_KEYS = (
    "new_violations",
    "new_accepted_issues",
    "new_security_hotspots",
    "new_coverage",
    "new_duplicated_lines_density",
    "new_lines",
)


def sonar_get(
    host: str, path: str, params: dict[str, str], token: str
) -> dict[str, Any]:
    """Call the Sonar web API. The token is optional for public projects."""
    response = requests.get(
        f"{host}/{path}",
        params=params,
        auth=(token, "") if token else None,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_author_avatar(author: str) -> str:
    """Get the avatar URL for a GitHub user."""
    response = requests.get(f"https://api.github.com/users/{author}", timeout=30)
    response.raise_for_status()
    return response.json()["avatar_url"]


def get_measure(measures: dict[str, Any], metric: str) -> str | None:
    """Read one measure from an api/measures/component response.

    New code measures arrive under ``periods[0].value`` on Sonar Cloud or
    ``period.value`` on newer Sonar Server; plain measures use ``value``. A
    metric Sonar could not compute is absent from the response altogether,
    which is reported back as ``None`` rather than zero.
    """
    for measure in measures.get("component", {}).get("measures", []):
        if measure["metric"] != metric:
            continue
        if "value" in measure:
            return measure["value"]
        periods = measure.get("periods") or []
        if periods:
            return periods[0].get("value")
        return (measure.get("period") or {}).get("value")
    return None


def get_count(measures: dict[str, Any], metric: str) -> str:
    """Read a counter measure, defaulting to zero when Sonar omits it."""
    return get_measure(measures, metric) or "0"


def get_percentage(measures: dict[str, Any], metric: str) -> str:
    """Read a ratio measure, formatted as a percentage or as ``n/a``."""
    value = get_measure(measures, metric)
    return f"{float(value):.1f}%" if value is not None else "n/a"


def get_badge_info(quality_gate_status: str) -> tuple[str, str, str]:
    """Get badge text, badge style and gate wording from the gate status."""
    if quality_gate_status == "OK":
        return "Passed", "Good", "✅ Passed"
    if quality_gate_status == "ERROR":
        return "Failed", "Attention", "❌ Failed"
    return "No data", "Warning", "⚠️ Not computed"


def create_adaptive_card(
    bot_image_url: str,
    repo: str,
    project_label: str,
    pr_number: str,
    pr_title: str,
    pr_author: str,
    author_avatar_url: str,
    pr_url: str,
    analysis_url: str,
    badge_text: str,
    badge_style: str,
    gate_text: str,
    new_issues: str,
    accepted_issues: str,
    security_hotspots: str,
    coverage: str,
    duplications: str,
    note: str,
) -> dict[str, Any]:
    """Create the adaptive card JSON payload."""
    body = [
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
                        {
                            "type": "TextBlock",
                            "text": f"**Sonar Quality Gate — {project_label}**",
                            "wrap": True,
                        },
                        {
                            "type": "TextBlock",
                            "text": f"**{repo}**",
                            "wrap": True,
                            "color": "Good",
                        },
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
        {
            "type": "TextBlock",
            "text": f"#{pr_number} - {pr_title}",
            "wrap": True,
            "size": "ExtraLarge",
            "weight": "Bolder",
            "color": "Accent",
        },
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [
                        {
                            "type": "Image",
                            "url": author_avatar_url,
                            "size": "Small",
                            "style": "Person",
                        }
                    ],
                },
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"**{pr_author}** · **{project_label}** analysis",
                            "size": "Large",
                            "wrap": True,
                            "spacing": "Small",
                        }
                    ],
                },
            ],
        },
    ]

    if note:
        body.append(
            {
                "type": "TextBlock",
                "text": note,
                "wrap": True,
                "spacing": "Small",
                "isSubtle": True,
            }
        )

    body.append(
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"**Quality gate:** {gate_text}",
                            "wrap": True,
                            "spacing": "Small",
                        },
                        {
                            "type": "TextBlock",
                            "text": f"**New issues:** {new_issues}",
                            "wrap": True,
                            "spacing": "Small",
                        },
                        {
                            "type": "TextBlock",
                            "text": f"**Accepted issues:** {accepted_issues}",
                            "wrap": True,
                            "spacing": "Small",
                        },
                    ],
                    "verticalContentAlignment": "Center",
                },
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"**Security hotspots:** {security_hotspots}",
                            "wrap": True,
                            "spacing": "Small",
                        },
                        {
                            "type": "TextBlock",
                            "text": f"**Coverage on new code:** {coverage}",
                            "wrap": True,
                            "spacing": "Small",
                        },
                        {
                            "type": "TextBlock",
                            "text": f"**Duplications on new code:** {duplications}",
                            "wrap": True,
                            "spacing": "Small",
                        },
                    ],
                    "verticalContentAlignment": "Center",
                },
            ],
        }
    )

    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
                    "speak": f"Sonar quality gate {badge_text} for {project_label}",
                    "type": "AdaptiveCard",
                    "version": "1.5",
                    "body": body,
                    "msteams": {"width": "full"},
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "View Sonar analysis",
                            "url": analysis_url,
                        },
                        {
                            "type": "Action.OpenUrl",
                            "title": "View pull request",
                            "url": pr_url,
                        },
                    ],
                    "msTeams": {"width": "full"},
                },
            }
        ],
    }


def main():
    # Get environment variables
    webhook_url = os.environ["WEBHOOK_URL"]
    bot_image_url = os.environ["BOT_IMAGE_URL"]
    repo = os.environ["REPO"]
    project_key = os.environ["PROJECT_KEY"]
    project_label = os.environ["PROJECT_LABEL"]
    pr_number = os.environ["PR_NUMBER"]
    pr_title = os.environ["PR_TITLE"]
    pr_author = os.environ["PR_AUTHOR"]
    pr_url = os.environ["PR_URL"]
    sonar_token = os.environ.get("SONAR_TOKEN", "")
    sonar_host = os.environ.get("SONAR_HOST", "https://sonarcloud.io").rstrip("/")
    note = os.environ.get("NOTE", "")

    # Read the gate result and the new code measures for this pull request
    quality_gate = sonar_get(
        sonar_host,
        "api/qualitygates/project_status",
        {"projectKey": project_key, "pullRequest": pr_number},
        sonar_token,
    )
    measures = sonar_get(
        sonar_host,
        "api/measures/component",
        {
            "component": project_key,
            "pullRequest": pr_number,
            "metricKeys": ",".join(METRIC_KEYS),
        },
        sonar_token,
    )

    badge_text, badge_style, gate_text = get_badge_info(
        quality_gate.get("projectStatus", {}).get("status", "NONE")
    )

    coverage = get_percentage(measures, "new_coverage")
    duplications = get_percentage(measures, "new_duplicated_lines_density")

    # Sonar omits the new code ratios when the pull request adds no analysable
    # lines, which the Sonar UI shows as "There are not enough lines to compute
    # coverage".
    if get_count(measures, "new_lines") == "0":
        coverage = f"{coverage} _(no new lines)_"
        duplications = f"{duplications} _(no new lines)_"

    # Get author avatar
    author_avatar_url = get_author_avatar(pr_author)

    # Create payload
    payload = create_adaptive_card(
        bot_image_url=bot_image_url,
        repo=repo,
        project_label=project_label,
        pr_number=pr_number,
        pr_title=pr_title,
        pr_author=pr_author,
        author_avatar_url=author_avatar_url,
        pr_url=pr_url,
        analysis_url=f"{sonar_host}/summary/new_code?id={project_key}&pullRequest={pr_number}",
        badge_text=badge_text,
        badge_style=badge_style,
        gate_text=gate_text,
        new_issues=get_count(measures, "new_violations"),
        accepted_issues=get_count(measures, "new_accepted_issues"),
        security_hotspots=get_count(measures, "new_security_hotspots"),
        coverage=coverage,
        duplications=duplications,
        note=note,
    )

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
