import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Annotated

import typer
from dateutil.relativedelta import relativedelta
from fastapi import status
from httpx import HTTPStatusError, ReadTimeout

from app.api_clients.optscale import OptscaleClient
from app.conf import Settings
from app.db.base import session_factory
from app.db.handlers import DatasourceExpenseHandler, OrganizationHandler
from app.db.models import DatasourceExpense, Organization
from app.enums import DatasourceType, OrganizationStatus
from app.notifications import send_exception, send_info
from app.telemetry import capture_telemetry_cli_command

logger = logging.getLogger(__name__)


@dataclass
class OrganizationResult:
    """Outcome of processing organization expenses, aggregated for the final notification."""

    organization_id: str
    datasource_count: int = 0
    succeeded: bool = True
    error: str | None = None


@dataclass(frozen=True)
class ExpensePeriod:
    """Dates a single run targets: current month (today) and the daily figure (yesterday)."""

    today: date
    yesterday: date
    day_start: int
    day_end: int

    @classmethod
    def for_now(cls, now: datetime) -> "ExpensePeriod":
        today = now.date()
        yesterday = today - relativedelta(days=1)
        day_start = int(
            datetime(
                yesterday.year, yesterday.month, yesterday.day, 0, 0, 0, tzinfo=UTC
            ).timestamp()
        )
        day_end = int(
            datetime(
                yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, tzinfo=UTC
            ).timestamp()
        )
        return cls(today=today, yesterday=yesterday, day_start=day_start, day_end=day_end)


def filter_relevant_datasources(datasources: list[dict]) -> list[dict]:
    result = []

    for datasource in datasources:
        if datasource["type"] in ["azure_tenant", "gcp_tenant"]:
            logger.warning(
                "Skipping child datasource %s of type %s since it's a child datasource "
                "and its expenses will always be zero",
                datasource["id"],
                datasource["type"],
            )
            continue

        result.append(datasource)

    return result


async def fetch_daily_organization_expenses(
    organization: Organization,
    optscale_client: OptscaleClient,
    day_start: int,
    day_end: int,
) -> list[dict]:
    expenses: list[dict] = []

    try:
        logger.info("Fetching daily expenses for organization %s", organization.id)
        response = await optscale_client.fetch_daily_expenses_for_organization(
            organization.linked_organization_id,  # ty: ignore[invalid-argument-type]
            day_start,
            day_end,
        )

        response_datasources = response.json()["counts"].values()
        logger.info(
            "Fetched %d daily datasources expenses for organization %s - %s",
            len(response_datasources),
            organization.id,
            organization.name,
        )

        expenses = filter_relevant_datasources(response_datasources)
    except (HTTPStatusError, ReadTimeout) as exc:
        if isinstance(exc, HTTPStatusError) and exc.response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_424_FAILED_DEPENDENCY,
        ]:
            logger.warning(
                f"Organization {organization.id} not found or "
                "organization doesn't have any cloud accounts connected in Optscale."
            )
        else:
            msg = (
                "Unexpected error occurred fetching daily "
                f"expenses for organization {organization.id}"
            )
            logger.exception(msg)
            await send_exception("Datasource Expenses Update Error", f"{msg}: {exc}")

    return expenses


async def fetch_total_monthly_organization_expenses(
    organization: Organization,
    optscale_client: OptscaleClient,
) -> list[dict]:
    expenses: list[dict] = []

    try:
        logger.info("Fetching monthly expenses for organization %s", organization.id)
        response = await optscale_client.fetch_datasources_for_organization(
            organization.linked_organization_id,  # ty: ignore[invalid-argument-type]
        )

        response_datasources = response.json()["cloud_accounts"]
        logger.info(
            "Fetched %d monthly datasource expenses for organization %s - %s",
            len(response_datasources),
            organization.id,
            organization.name,
        )

        expenses = filter_relevant_datasources(response_datasources)
    except (HTTPStatusError, ReadTimeout) as exc:
        if (
            isinstance(exc, HTTPStatusError)
            and exc.response.status_code == status.HTTP_404_NOT_FOUND
        ):
            msg = f"Organization {organization.id} not found on Optscale."
            logger.warning(msg)
        else:
            msg = (
                f"Unexpected error occurred fetching datasources for organization {organization.id}"
            )
            logger.exception(msg)
            await send_exception("Datasource Expenses Update Error", f"{msg}: {exc}")

    return expenses


async def store_organization_expenses(
    datasource_expense_handler: DatasourceExpenseHandler,
    organization_id: str,
    expenses: list[dict],
    year: int,
    month: int,
    day: int,
    is_daily: bool = False,
) -> int:
    for expense in expenses:
        defaults = {
            "datasource_name": expense["name"],
            "linked_datasource_id": expense["id"],
            "linked_datasource_type": expense["type"],
        }
        if is_daily:
            defaults["expenses"] = expense["total"]
            existing_ds_expense = await datasource_expense_handler.first(
                where_clauses=[
                    DatasourceExpense.datasource_id == expense["account_id"],
                    DatasourceExpense.organization_id == organization_id,
                    DatasourceExpense.year == year,
                    DatasourceExpense.month == month,
                    DatasourceExpense.day == day,
                    DatasourceExpense.linked_datasource_type.in_(
                        [DatasourceType.UNKNOWN, expense["type"]]
                    ),
                ],
            )
            created = False
        else:
            defaults["total_expenses"] = expense["details"]["cost"]
            existing_ds_expense, created = await datasource_expense_handler.get_or_create(
                datasource_id=expense["account_id"],
                organization_id=organization_id,
                year=year,
                month=month,
                day=day,
                defaults=defaults,
                extra_conditions=[
                    DatasourceExpense.linked_datasource_type.in_(
                        [DatasourceType.UNKNOWN, expense["type"]]
                    )
                ],
            )

        if not created and existing_ds_expense:
            await datasource_expense_handler.update(existing_ds_expense, defaults)
    return len(expenses)


async def process_organization(
    organization: Organization,
    settings: Settings,
    period: ExpensePeriod,
    semaphore: asyncio.Semaphore,
) -> OrganizationResult:
    result = OrganizationResult(organization_id=organization.id)

    async with semaphore:
        try:
            async with OptscaleClient(settings) as optscale_client:
                monthly_expenses = await fetch_total_monthly_organization_expenses(
                    organization, optscale_client
                )
                daily_expenses = await fetch_daily_organization_expenses(
                    organization, optscale_client, period.day_start, period.day_end
                )

            async with session_factory() as session:
                datasource_expense_handler = DatasourceExpenseHandler(session)
                async with session.begin():
                    monthly_count = await store_organization_expenses(
                        datasource_expense_handler,
                        organization.id,
                        monthly_expenses,
                        year=period.today.year,
                        month=period.today.month,
                        day=period.today.day,
                        is_daily=False,
                    )
                    daily_count = await store_organization_expenses(
                        datasource_expense_handler,
                        organization.id,
                        daily_expenses,
                        year=period.yesterday.year,
                        month=period.yesterday.month,
                        day=period.yesterday.day,
                        is_daily=True,
                    )
                result.datasource_count = monthly_count + daily_count

        except Exception as exc:
            logger.exception(f"Failed to process organization {organization.id}: {exc}")
            result.succeeded = False
            result.error = str(exc)

    return result


@capture_telemetry_cli_command(__name__, "Update Current Month Datasource Expenses")
async def main(settings: Settings, organization_id: str | None = None) -> None:
    period = ExpensePeriod.for_now(datetime.now(UTC))
    semaphore = asyncio.Semaphore(settings.max_parallel_tasks)

    async with session_factory() as session:
        logger.info("Querying organizations")
        organization_handler = OrganizationHandler(session)
        where_clauses = [Organization.status != OrganizationStatus.DELETED]
        if organization_id:
            where_clauses.append(Organization.id == organization_id)

        organizations = await organization_handler.query_db(where_clauses=where_clauses)
        logger.info(f"Found {len(organizations)} organizations to process")

    not_linked_orgs = [org.id for org in organizations if org.linked_organization_id is None]
    if len(not_linked_orgs) > 0:
        logger.warning(
            f"Found {len(not_linked_orgs)} organizations without "
            f"linked organization ID: {not_linked_orgs}. Skipping..."
        )

    tasks = [
        asyncio.create_task(process_organization(org, settings, period, semaphore))
        for org in organizations
        if org.linked_organization_id is not None
    ]
    results = await asyncio.gather(*tasks)

    succeeded = [r for r in results if r.succeeded]
    failed = [r for r in results if not r.succeeded]
    total_ds = sum(r.datasource_count for r in succeeded)

    if failed:
        detail = "; ".join(f"{r.organization_id}: {r.error}" for r in failed)
        msg = (
            f"Datasource expenses updated for {len(succeeded)} organizations "
            f"({total_ds} data sources expenses processed). {len(failed)} failed: {detail}"
        )
        logger.warning(msg)
        await send_exception("Datasource Expenses Update Partial Failure", msg)
    else:
        msg = (
            f"Datasource expenses updated for {len(succeeded)} organizations "
            f"({total_ds} data sources expenses processed)."
        )
        logger.info(msg)
        await send_info("Datasource Expenses Update Success", msg)


def command(
    ctx: typer.Context,
    organization: Annotated[
        str | None,
        typer.Option(
            "--organization",
            "-o",
            help="Organization ID. Default: all organizations",
        ),
    ] = None,
) -> None:
    """
    Fetch from Optscale all datasource expenses for the current month
    and store them in the database.
    """
    logger.info("Starting command function")
    asyncio.run(main(ctx.obj, organization))
    logger.info("Completed command function")
