import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
import typer
from httpx import HTTPStatusError, ReadTimeout
from sqlalchemy.exc import DatabaseError

from app.api_clients.ffc_api import FFCAPIClient
from app.api_clients.optscale import OptscaleClient
from app.conf import Settings
from app.db.base import session_factory
from app.db.handlers import EntitlementHandler, OrganizationHandler
from app.db.models import Entitlement, Organization
from app.enums import EntitlementStatus, OrganizationStatus
from app.notifications import (
    ColumnHeader,
    NotificationDetails,
    send_exception,
    send_info,
)
from app.telemetry import capture_telemetry_cli_command

logger = logging.getLogger(__name__)


@dataclass
class RedeemResult:
    """Outcome of redeeming entitlements for a single organization, aggregated for notifications."""

    organization_id: str
    redeemed_rows: list[tuple[str, str, str, str]] = field(default_factory=list)
    succeeded: bool = True
    error: str | None = None


async def fetch_datasources_for_organization(settings: Settings, organization_id: str) -> dict:
    async with OptscaleClient(settings) as optscale_client:
        response = await optscale_client.fetch_datasources_for_organization(
            organization_id,  # type: ignore[arg-type]
            details=False,
        )
    return response.json()["cloud_accounts"]


async def create_entitlement_tag_for_datasource(
    ffc_api_client: FFCAPIClient,
    entitlement_id: str,
    datasource_id: str,
) -> None:
    try:
        await ffc_api_client.create_tag_for_datasource(
            datasource_id=datasource_id,
            name="entitlement",
            value=entitlement_id,
        )
    except (HTTPStatusError, ReadTimeout) as exc:
        logger.warning(f"Could not create entitlement tag for datasource {datasource_id}: {exc}")


async def process_datasource(
    datasource: dict,
    organization: Organization,
    entitlement_handler: EntitlementHandler,
    ffc_api_client: FFCAPIClient,
) -> tuple[str, str, str, str] | None:
    datasource_id = datasource["account_id"]
    datasource_type = datasource["type"]
    datasource_name = datasource["name"]
    match datasource_type:
        case "azure_tenant" | "gcp_tenant":
            logger.debug(
                f"Found {datasource_id} {datasource_name} of type {datasource_type}, "
                "skip containers!"
            )
            return None
        case "azure_cnr" | "aws_cnr" | "gcp_cnr":
            type_name = datasource["type"].split("_")[0].capitalize()
            logger.info(
                f"Found {type_name} datasource: {datasource['account_id']} {datasource['name']}"
            )
        case _:
            logger.warning(
                f"Found {datasource_id} {datasource_name} of type {datasource_type}, "
                "unsupported type!"
            )
            return None

    instance = await entitlement_handler.first(
        where_clauses=[
            Entitlement.datasource_id == datasource_id,
            Entitlement.status == EntitlementStatus.NEW,
        ]
    )
    if instance:
        await entitlement_handler.update(
            instance,
            data={
                "status": EntitlementStatus.ACTIVE,
                "redeemed_at": instance.redeem_at or datetime.now(UTC),
                "redeemed_by": organization,
                "linked_datasource_id": datasource["id"],
                "linked_datasource_type": datasource["type"],
                "linked_datasource_name": datasource["name"],
            },
        )
        await create_entitlement_tag_for_datasource(
            ffc_api_client=ffc_api_client,
            entitlement_id=instance.id,
            datasource_id=datasource["id"],
        )
        logger.info(
            f"The entitlement {instance.id} - {instance.name} "
            f"owned by {instance.owner.id} - {instance.owner.name} "
            f"has been redeemed by {organization.id} - {organization.name} "
            f"for datasource {datasource_id} - {datasource_name}."
        )
        return (
            f"{instance.id}\t/\t{instance.name}",
            f"{instance.owner.id}\t/\t{instance.owner.name}",
            f"{organization.id}\t/\t{organization.name}",
            f"{datasource_id}\t/\t{datasource_name}",
        )
    else:
        logger.info(f"Entitlement not found for datasource {datasource_id} - {datasource_name}.")
        return None


async def process_organization(
    organization: Organization,
    settings: Settings,
    semaphore: asyncio.Semaphore,
) -> RedeemResult:
    result = RedeemResult(organization_id=organization.id)

    async with semaphore:
        logger.info(
            f"Fetching datasources for organization: {organization.id} - {organization.name}..."
        )
        try:
            datasources = await fetch_datasources_for_organization(
                settings,
                organization.linked_organization_id,  # type: ignore[arg-type]
            )

            async with session_factory() as session, FFCAPIClient(settings) as ffc_api_client:
                entitlement_handler = EntitlementHandler(session)
                async with session.begin():
                    for datasource in datasources:
                        row = await process_datasource(
                            datasource,
                            organization,
                            entitlement_handler,
                            ffc_api_client,
                        )
                        if row is not None:
                            result.redeemed_rows.append(row)

        except (httpx.HTTPError, httpx.ReadTimeout) as e:
            message = (
                f"Failed to fetch datasources for organization {organization.id} "
                f"({type(e).__name__}): {str(e) or repr(e)}"
            )
            logger.error(message)
            result.succeeded = False
            result.error = str(message)
        except DatabaseError as e:  # pragma: no cover
            message = (
                f"Failed to process or update datasources "
                f"for organization {organization.id}: {str(e)}"
            )
            logger.error(message)
            result.succeeded = False
            result.error = str(message)

    return result


async def notify_results(results: Sequence[RedeemResult]) -> None:
    redeemed = [row for result in results if result.succeeded for row in result.redeemed_rows]
    failed = [result for result in results if not result.succeeded]

    if redeemed:
        msg = "Entitlement has" if len(redeemed) == 1 else "Entitlements have"
        msg = f"{len(redeemed)} {msg} been successfully redeemed."
        await send_info(
            "Redeem Entitlements Success",
            msg,
            details=NotificationDetails(
                header=(
                    ColumnHeader("Entitlement", width="stretch"),
                    ColumnHeader("Owner", width="stretch"),
                    ColumnHeader("Organization", width="stretch"),
                    ColumnHeader("Datasource", width="stretch"),
                ),
                rows=redeemed,
            ),
        )
    if failed:
        detail = "; ".join(f"{result.organization_id}: {result.error}" for result in failed)
        await send_exception(
            "Redeem Entitlements Error",
            f"{len(failed)} organizations failed to process: {detail}",
        )


@capture_telemetry_cli_command(__name__, "Redeem Entitlements")
async def redeem_entitlements(settings: Settings):
    semaphore = asyncio.Semaphore(settings.max_parallel_tasks)

    async with session_factory() as session:
        organization_handler = OrganizationHandler(session)
        organizations = await organization_handler.query_db(
            where_clauses=[Organization.status == OrganizationStatus.ACTIVE],
            order_by=[Organization.created_at],
        )

    tasks = [
        asyncio.create_task(process_organization(organization, settings, semaphore))
        for organization in organizations
    ]

    results = await asyncio.gather(*tasks)
    await notify_results(results)


def command(ctx: typer.Context):
    """Redeem entitlements for an Organization."""
    asyncio.run(redeem_entitlements(ctx.obj))
