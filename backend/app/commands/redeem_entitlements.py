import asyncio
import logging
from datetime import UTC, datetime

import httpx
import typer
from sqlalchemy.exc import DatabaseError

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

BATCH_SIZE = 100


async def fetch_datasources_for_organization(settings: Settings, organization_id: str) -> dict:
    client = OptscaleClient(settings)
    response = await client.fetch_datasources_for_organization(organization_id, details=False)
    return response.json()["cloud_accounts"]


async def process_datasource(
    datasource: dict,
    organization: Organization,
    entitlement_handler: EntitlementHandler,
):
    datasource_id = datasource["account_id"]
    datasource_type = datasource["type"]
    datasource_name = datasource["name"]
    type_name = datasource_type.split("_")[0].capitalize()
    match datasource_type:
        case "azure_tenant" | "gcp_tenant":
            logger.debug(
                f"Found {datasource_id} {datasource_name} of type {datasource_type}, "
                "skip containers!"
            )
            return
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
            return
    try:
        instance = await entitlement_handler.first(
            where_clauses=[
                Entitlement.datasource_id == datasource_id,
                Entitlement.status == EntitlementStatus.NEW,
            ]
        )
        if instance:
            updated_entitlement = await entitlement_handler.update(
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
            msg = (
                f"The entitlement {instance.id} - {instance.name} "
                f"owned by {instance.owner.id} - {instance.owner.name} "
                f"has been redeemed by {organization.id} - {organization.name} "
                f"for datasource {datasource_id} - {datasource_name}."
            )
            logger.info(msg)
            return updated_entitlement
        else:
            logger.info(
                f"Entitlement not found for datasource {datasource_id} - {datasource_name}."
            )

    except DatabaseError as e:  # pragma: no cover
        msg = (
            f"An error occurred while updating the entitlement for "
            f"{datasource_id} - {datasource_name}: {e}"
        )
        logger.error(msg)
        await send_exception("Redeem Entitlements Error", msg)


@capture_telemetry_cli_command(__name__, "Redeem Entitlements")
async def redeem_entitlements(settings: Settings):
    # FIXME: Long-lived DB transaction (making API calls inside the transaction)

    async with session_factory.begin() as session:
        organization_handler = OrganizationHandler(session)
        entitlement_handler = EntitlementHandler(session)

        async for organization in organization_handler.stream_scalars(
            extra_conditions=[Organization.status == OrganizationStatus.ACTIVE],
            order_by=[Organization.created_at],
            batch_size=BATCH_SIZE,
        ):
            logger.info(
                f"Fetching datasources for organization: {organization.id} - {organization.name}..."
            )
            datasources = None
            try:
                datasources = await fetch_datasources_for_organization(
                    settings,
                    organization.linked_organization_id,  # type: ignore
                )
            except (httpx.HTTPError, httpx.ReadTimeout) as e:
                message = (
                    f"Failed to fetch datasources for organization {organization.id} "
                    f"({type(e).__name__}): {str(e) or repr(e)}"
                )
                logger.error(message)
                await send_exception("Redeem Entitlements Error", message)
                continue
            redeemed_entitlements = []
            for datasource in datasources:
                entitlement = await process_datasource(
                    datasource,
                    organization,
                    entitlement_handler,
                )
                if entitlement:
                    redeemed_entitlements.append(entitlement)

            if len(redeemed_entitlements) > 0:
                msg = "Entitlement has" if len(redeemed_entitlements) == 1 else "Entitlements have"
                msg = f"{len(redeemed_entitlements)} {msg} been successfully redeemed."
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
                        rows=[
                            (
                                f"{ent.id}\t/\t{ent.name}",
                                f"{ent.owner.id}\t/\t{ent.owner.name}",
                                f"{ent.redeemed_by.id}\t/\t{ent.redeemed_by.name}",  # type: ignore
                                f"{ent.datasource_id}\t/\t{ent.linked_datasource_name}",
                            )
                            for ent in redeemed_entitlements
                        ],
                    ),
                )


def command(ctx: typer.Context):
    """Redeem entitlements for an Organization."""
    asyncio.run(redeem_entitlements(ctx.obj))
