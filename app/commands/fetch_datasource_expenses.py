import asyncio
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
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
            organization.linked_organization_id,  # type: ignore[arg-type]
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
            organization.linked_organization_id,  # type: ignore[arg-type]
        )

        response_datasources = response.json()["cloud_accounts"]
        logger.info(
            "Fetched %d datasources for organization %s - %s",
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


async def fetch_datasource_expenses(
    organizations: Sequence[Organization],
    optscale_client: OptscaleClient,
    year: int,
    month: int,
    day: int,
    is_daily: bool = False,
) -> dict[str, list[dict]]:
    expenses: dict[str, list[dict]] = {}
    day_start = int((datetime(year, month, day, 0, 0, 0, tzinfo=UTC)).timestamp())
    day_end = int((datetime(year, month, day, 23, 59, 59, tzinfo=UTC)).timestamp())

    for organization in organizations:
        if organization.linked_organization_id is None:
            logger.warning(
                "Organization %s - %s has no linked organization ID. Skipping...",
                organization.id,
                organization.name,
            )
            continue

        if is_daily:
            organization_expenses = await fetch_daily_organization_expenses(
                organization,
                optscale_client,
                day_start,
                day_end,
            )
        else:
            organization_expenses = await fetch_total_monthly_organization_expenses(
                organization,
                optscale_client,
            )
        expenses[organization.id] = organization_expenses

    return expenses


async def store_datasource_expenses(
    datasource_expense_handler: DatasourceExpenseHandler,
    expenses_per_organization: dict[str, list[dict]],
    year: int,
    month: int,
    day: int,
    is_daily: bool = False,
) -> None:
    org_count = 0
    ds_count = 0

    for organization_id, datasources in expenses_per_organization.items():
        org_count += 1
        ds_count += len(datasources)

        for datasource in datasources:
            defaults = {
                "datasource_name": datasource["name"],
                "linked_datasource_id": datasource["id"],
                "linked_datasource_type": datasource["type"],
            }
            if is_daily:
                defaults["expenses"] = datasource["total"]

                existing_ds_expense = await datasource_expense_handler.first(
                    where_clauses=[
                        DatasourceExpense.datasource_id == datasource["account_id"],
                        DatasourceExpense.organization_id == organization_id,
                        DatasourceExpense.year == year,
                        DatasourceExpense.month == month,
                        DatasourceExpense.day == day,
                        DatasourceExpense.linked_datasource_type.in_(
                            [DatasourceType.UNKNOWN, datasource["type"]]
                        ),
                    ],
                )
                created = False
            else:
                defaults["total_expenses"] = datasource["details"]["cost"]

                existing_ds_expense, created = await datasource_expense_handler.get_or_create(
                    datasource_id=datasource["account_id"],
                    organization_id=organization_id,
                    year=year,
                    month=month,
                    day=day,
                    defaults=defaults,
                    extra_conditions=[
                        DatasourceExpense.linked_datasource_type.in_(
                            [DatasourceType.UNKNOWN, datasource["type"]]
                        )
                    ],
                )

            if not created and existing_ds_expense:
                await datasource_expense_handler.update(
                    existing_ds_expense,
                    defaults,
                )
    msg = (
        f"{'Daily' if is_daily else 'Monthly'} expenses of {ds_count} datasources "
        f"configured by {org_count} Organizations have been updated."
    )
    logger.info(msg)
    await send_info("Datasource Expenses Update Success", msg)


@capture_telemetry_cli_command(__name__, "Update Current Month Datasource Expenses")
async def main(settings: Settings, organization_id: str | None = None) -> None:
    today = datetime.now(UTC).date()
    yesterday = today - relativedelta(days=1)

    async with session_factory() as session:
        datasource_expense_handler = DatasourceExpenseHandler(session)
        organization_handler = OrganizationHandler(session)

        async with session.begin():
            if organization_id:
                logger.info(f"Querying for provided organization {organization_id}")
                organizations = await organization_handler.query_db(
                    where_clauses=[
                        Organization.id == organization_id,
                        Organization.status != OrganizationStatus.DELETED,
                    ],
                )
            else:
                logger.info("Querying organizations")
                organizations = await organization_handler.query_db(
                    where_clauses=[Organization.status != OrganizationStatus.DELETED]
                )
            logger.info("Found %d organizations to process", len(organizations))

        for day, is_daily, frq in [
            (today, False, "monthly"),
            (yesterday, True, "daily"),
        ]:
            async with OptscaleClient(settings) as optscale_client:
                logger.info(
                    f"Fetching {frq} datasources expenses for the organizations from Optscale"
                )
                expenses = await fetch_datasource_expenses(
                    organizations, optscale_client, day.year, day.month, day.day, is_daily=is_daily
                )
                logger.info(f"Completed fetching {frq} expenses")

            async with session.begin():
                logger.info(
                    "Storing %s datasource expenses for %s organiziations for %s",
                    frq,
                    len(organizations),
                    today.strftime("%d %B %Y"),  # e.g. "20 March 2025"
                )
                await store_datasource_expenses(
                    datasource_expense_handler,
                    expenses,
                    year=day.year,
                    month=day.month,
                    day=day.day,
                    is_daily=is_daily,
                )

                logger.info(f"Completed storing {frq} datasource expenses")


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
