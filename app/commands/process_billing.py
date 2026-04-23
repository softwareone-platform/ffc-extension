import asyncio
import logging
from datetime import date
from typing import Annotated

import typer
from dateutil.relativedelta import relativedelta

from app.billing.constants import LOWER_BILLING_YEAR
from app.billing.process_billing import process_billing
from app.conf import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


def command(
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Test generation of billing files without making changes.",
        ),
    ] = False,
    authorization: Annotated[
        str | None,
        typer.Option(
            "--authorization",
            help="Generate billing file for given authorization.",
        ),
    ] = None,
    year: Annotated[
        int | None,
        typer.Option(
            "--year",
            help="Year for billing period. Defaults to previous month's year.",
        ),
    ] = None,
    month: Annotated[
        int | None,
        typer.Option(
            "--month",
            help="Month for billing period. Defaults to previous month.",
        ),
    ] = None,
    cutoff_day: Annotated[
        int,
        typer.Option(
            "--cutoff-day",
            help="The cutoff day to run the process for. Default is 5.",
        ),
    ] = 5,
) -> None:
    """Generate billing files for a given period."""

    today = date.today()
    previous_month = today - relativedelta(months=1)

    billing_year = year if year is not None else previous_month.year
    billing_month = month if month is not None else previous_month.month

    if billing_year < LOWER_BILLING_YEAR:
        typer.secho(
            f"The billing year must be {LOWER_BILLING_YEAR} or later.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    if not (1 <= cutoff_day <= 28):
        typer.secho(
            "The cutoff-day must be between 1 and 28 (inclusive).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    if not (1 <= billing_month <= 12):
        typer.secho(
            "The billing month must be between 1 and 12 (inclusive).",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    if (billing_year, billing_month) > (today.year, today.month):
        typer.secho(
            "The billing period cannot be in the future.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    logger.info(
        "Starting process billing for %04d-%02d (cutoff_day=%d, dry_run=%s, authorization=%s)",
        billing_year,
        billing_month,
        cutoff_day,
        dry_run,
        authorization,
    )

    asyncio.run(
        process_billing(
            year=billing_year,
            month=billing_month,
            cutoff_day=cutoff_day,
            authorization_id=authorization,
            dry_run=dry_run,
        )
    )

    logger.info("Completed process billing command")
