from typing import Any

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from app.cli import app


def _build_args(opts: dict[str, Any]) -> list[str]:
    args = ["process-billing"]
    if opts.get("dry_run"):
        args.append("--dry-run")
    if "authorization" in opts:
        args += ["--authorization", opts["authorization"]]
    if "year" in opts:
        args += ["--year", str(opts["year"])]
    if "month" in opts:
        args += ["--month", str(opts["month"])]
    if "cutoff_day" in opts:
        args += ["--cutoff-day", str(opts["cutoff_day"])]
    return args


@pytest.mark.parametrize(
    ("opts", "not_allowed", "error_message"),
    [
        (
            {"year": 2025, "month": 8, "dry_run": True, "cutoff_day": 1},
            False,
            None,
        ),
        (
            {
                "year": 2025,
                "month": 12,
                "dry_run": False,
                "authorization": "AUTH123",
                "cutoff_day": 1,
            },
            False,
            None,
        ),
        (
            {
                "year": 2027,
                "month": 1,
                "dry_run": True,
                "cutoff_day": 5,
            },
            True,
            "The billing period cannot be in the future.",
        ),
        (
            {
                "year": 2026,
                "month": 4,
                "dry_run": True,
                "cutoff_day": 5,
            },
            True,
            "The billing period cannot be in the future.",
        ),
        (
            {
                "dry_run": True,
            },
            False,
            None,
        ),
        (
            {
                "year": 2026,
                "dry_run": True,
                "cutoff_day": 5,
            },
            False,
            None,
        ),
        (
            {
                "month": 2,
                "dry_run": True,
                "cutoff_day": 5,
            },
            False,
            None,
        ),
        (
            {
                "month": 20,
                "dry_run": True,
            },
            True,
            "The billing month must be between 1 and 12 (inclusive).",
        ),
        (
            {
                "cutoff_day": 100,
                "dry_run": True,
            },
            True,
            "The cutoff-day must be between 1 and 28 (inclusive).",
        ),
        (
            {
                "year": 2024,
                "month": 12,
                "dry_run": True,
                "cutoff_day": 5,
            },
            True,
            "The billing year must be",
        ),
    ],
)
@freeze_time("2026-03-16")
def test_process_billing_command(
    mocker: MockerFixture,
    opts: dict[str, Any],
    not_allowed: bool,
    error_message: str | None,
) -> None:
    mock_coro = mocker.MagicMock()
    mock_process_billing = mocker.MagicMock(return_value=mock_coro)
    mocker.patch("app.commands.process_billing.process_billing", mock_process_billing)
    mock_run = mocker.patch("app.commands.process_billing.asyncio.run")

    runner = CliRunner()
    result = runner.invoke(app, _build_args(opts))

    if not_allowed:
        assert result.exit_code == 1
        if error_message:
            assert error_message in result.stderr
        mock_process_billing.assert_not_called()
        mock_run.assert_not_called()
    else:
        assert result.exit_code == 0
        mock_process_billing.assert_called_once_with(
            year=opts.get("year", 2026),
            month=opts.get("month", 2),
            authorization_id=opts.get("authorization"),
            dry_run=opts.get("dry_run", False),
            cutoff_day=opts.get("cutoff_day", 5),
        )
        mock_run.assert_called_once_with(mock_coro)
