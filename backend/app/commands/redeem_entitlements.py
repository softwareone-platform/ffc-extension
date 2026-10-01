import asyncio
import logging
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
    send_warning,
)
from app.telemetry import capture_telemetry_cli_command

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


@dataclass
class DatasourceResult:
    """Outcome of processing a single datasource."""

    redeemed_entitlement: Entitlement | None = None
    duplicate_entitlements: list[Entitlement] = field(default_factory=list)


async def fetch_datasources_for_organization(settings: Settings, organization_id: str) -> dict:
    client = OptscaleClient(settings)
    response = await client.fetch_datasources_for_organization(organization_id, details=False)
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
) -> DatasourceResult:
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
            return DatasourceResult()
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
            return DatasourceResult()
    try:
        entitlements = await entitlement_handler.query_db(
            where_clauses=[
                Entitlement.datasource_id == datasource_id,
                Entitlement.status.in_((EntitlementStatus.NEW, EntitlementStatus.ACTIVE)),
            ],
            order_by=[Entitlement.created_at],
        )
        active_entitlements = [
            entitlement
            for entitlement in entitlements
            if entitlement.status == EntitlementStatus.ACTIVE
        ]
        new_entitlements = [
            entitlement
            for entitlement in entitlements
            if entitlement.status == EntitlementStatus.NEW
        ]

        if active_entitlements:
            if len(entitlements) > 1:
                logger.warning(
                    f"Found {len(entitlements)} duplicate entitlements "
                    f"({', '.join(entitlement.id for entitlement in entitlements)}) "
                    f"for datasource {datasource_id} - {datasource_name}, "
                    "one of them is already active: skipping."
                )
                return DatasourceResult(duplicate_entitlements=list(entitlements))

            logger.info(
                f"The entitlement {active_entitlements[0].id} - {active_entitlements[0].name} "
                f"is already active for datasource {datasource_id} - {datasource_name}: skipping."
            )
            return DatasourceResult()

        if not new_entitlements:
            logger.info(
                f"Entitlement not found for datasource {datasource_id} - {datasource_name}."
            )
            return DatasourceResult()

        duplicate_entitlements = list(new_entitlements) if len(new_entitlements) > 1 else []
        instance = new_entitlements[0]

        if duplicate_entitlements:
            logger.warning(
                f"Found {len(new_entitlements)} duplicate entitlements "
                f"({', '.join(entitlement.id for entitlement in new_entitlements)}) "
                f"for datasource {datasource_id} - {datasource_name}, "
                f"redeeming the oldest one: {instance.id}."
            )

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
        await create_entitlement_tag_for_datasource(
            ffc_api_client=ffc_api_client,
            entitlement_id=instance.id,
            datasource_id=datasource["id"],
        )
        msg = (
            f"The entitlement {instance.id} - {instance.name} "
            f"owned by {instance.owner.id} - {instance.owner.name} "
            f"has been redeemed by {organization.id} - {organization.name} "
            f"for datasource {datasource_id} - {datasource_name}."
        )
        logger.info(msg)
        return DatasourceResult(
            redeemed_entitlement=updated_entitlement,
            duplicate_entitlements=duplicate_entitlements,
        )

    except DatabaseError as e:  # pragma: no cover
        msg = (
            f"An error occurred while updating the entitlement for "
            f"{datasource_id} - {datasource_name}: {e}"
        )
        logger.error(msg)
        await send_exception("Redeem Entitlements Error", msg)
        return DatasourceResult()


async def notify_redeemed_entitlements(redeemed_entitlements: list[Entitlement]) -> None:
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


async def notify_duplicate_entitlements(
    organization: Organization,
    duplicate_entitlements: list[tuple[dict, list[Entitlement]]],
) -> None:
    msg = "datasource has" if len(duplicate_entitlements) == 1 else "datasources have"
    msg = (
        f"{len(duplicate_entitlements)} {msg} multiple entitlements in "
        f"`new` or `active` status for the organization "
        f"{organization.id} - {organization.name}."
    )
    await send_warning(
        "Redeem Entitlements Duplicates",
        msg,
        details=NotificationDetails(
            header=(
                ColumnHeader("Datasource", width="stretch"),
                ColumnHeader("Entitlement", width="stretch"),
                ColumnHeader("Owner", width="stretch"),
                ColumnHeader("Status", width="auto"),
            ),
            rows=[
                (
                    f"{datasource['account_id']}\t/\t{datasource['name']}",
                    f"{ent.id}\t/\t{ent.name}",
                    f"{ent.owner.id}\t/\t{ent.owner.name}",
                    ent.status.value,
                )
                for datasource, entitlements in duplicate_entitlements
                for ent in entitlements
            ],
        ),
    )


@capture_telemetry_cli_command(__name__, "Redeem Entitlements")
async def redeem_entitlements(settings: Settings):
    # FIXME: Long-lived DB transaction (making API calls inside the transaction)

    async with session_factory.begin() as session:
        organization_handler = OrganizationHandler(session)
        entitlement_handler = EntitlementHandler(session)
        ffc_api_client = FFCAPIClient(settings)

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
            duplicate_entitlements: list[tuple[dict, list[Entitlement]]] = []
            for datasource in datasources:
                result = await process_datasource(
                    datasource,
                    organization,
                    entitlement_handler,
                    ffc_api_client,
                )
                if result.redeemed_entitlement:
                    redeemed_entitlements.append(result.redeemed_entitlement)
                if result.duplicate_entitlements:
                    duplicate_entitlements.append((datasource, result.duplicate_entitlements))

            if len(redeemed_entitlements) > 0:
                await notify_redeemed_entitlements(redeemed_entitlements)

            if len(duplicate_entitlements) > 0:
                await notify_duplicate_entitlements(organization, duplicate_entitlements)


def command(ctx: typer.Context):
    """Redeem entitlements for an Organization."""
    asyncio.run(redeem_entitlements(ctx.obj))
