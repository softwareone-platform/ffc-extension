import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Annotated, Any, cast

import typer
from httpx import HTTPError
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from app.api_clients.ffc_api import FFCAPIClient
from app.api_clients.optscale import OptscaleClient
from app.conf import Settings
from app.db.base import session_factory
from app.db.handlers import EntitlementHandler
from app.db.models import Entitlement, Organization
from app.enums import EntitlementStatus, OrganizationStatus
from app.notifications import ColumnHeader, NotificationDetails, send_info, send_warning
from app.telemetry import capture_telemetry_cli_command

logger = logging.getLogger(__name__)

BATCH_SIZE = 100
ENTITLEMENT_TAG_NAME = "entitlement"
CONTAINER_DATASOURCE_TYPES = ("azure_tenant", "gcp_tenant")
NOTIFICATION_TITLE = "Sync Entitlements Datasources"


@dataclass
class EntitlementOutcome:
    """A notifiable outcome for an entitlement: a relink or an error."""

    entitlement: Entitlement
    details: str
    is_error: bool = False


@dataclass
class Results:
    relinked: int = 0
    tags_created: int = 0
    tags_deleted: int = 0
    datasources_not_found: int = 0
    terminated_organization_entitlements: int = 0
    failed: int = 0
    outcomes: list[EntitlementOutcome] = field(default_factory=list)

    def add_error(self, entitlement: Entitlement, details: str) -> None:
        self.outcomes.append(EntitlementOutcome(entitlement, details, is_error=True))


def format_exception(exc: Exception) -> str:
    return f"{type(exc).__name__}: {str(exc) or repr(exc)}"


async def fetch_datasources_by_account_id(
    optscale_client: OptscaleClient,
    linked_organization_id: str,
) -> dict[str, dict[str, Any]]:
    """Return the organization's Optscale datasources keyed by their `account_id`."""
    response = await optscale_client.fetch_datasources_for_organization(
        linked_organization_id, details=False
    )
    return {
        datasource["account_id"]: datasource
        for datasource in response.json()["cloud_accounts"]
        if datasource["type"] not in CONTAINER_DATASOURCE_TYPES
    }


async def fetch_entitlement_tags(
    ffc_api_client: FFCAPIClient,
    entitlement_ids: list[str],
) -> dict[str, list[dict[str, Any]]]:
    """Return every `entitlement` tag pointing to one of the given entitlements, by value."""
    tags: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for start in range(0, len(entitlement_ids), BATCH_SIZE):
        ids = ",".join(entitlement_ids[start : start + BATCH_SIZE])
        rql = f"and(eq(name,{ENTITLEMENT_TAG_NAME}),in(value,({ids})))"
        offset = 0
        while True:
            response = await ffc_api_client.get_tags(rql=rql, limit=BATCH_SIZE, offset=offset)
            items = response.json()["items"]
            for tag in items:
                tags[tag["value"]].append(tag)
            if len(items) < BATCH_SIZE:
                break
            offset += len(items)
    return tags


async def sync_entitlement(
    entitlement: Entitlement,
    datasource: dict[str, Any],
    tags: list[dict[str, Any]],
    entitlement_handler: EntitlementHandler,
    ffc_api_client: FFCAPIClient,
    results: Results,
    dry_run: bool,
) -> None:
    datasource_id = datasource["id"]

    if entitlement.linked_datasource_id != datasource_id:
        logger.info(
            "%s: datasource %s has been recreated, relinking from %s to %s.",
            entitlement.id,
            entitlement.datasource_id,
            entitlement.linked_datasource_id,
            datasource_id,
        )
        if not dry_run:
            await entitlement_handler.update(
                entitlement,
                data={
                    "linked_datasource_id": datasource_id,
                    "linked_datasource_type": datasource["type"],
                    "linked_datasource_name": datasource["name"],
                },
            )
        results.relinked += 1

    for tag in tags:
        if tag["resource_id"] == datasource_id:
            continue
        logger.info(
            "%s: deleting orphan tag %s pointing to datasource %s.",
            entitlement.id,
            tag["id"],
            tag["resource_id"],
        )
        if not dry_run:
            await ffc_api_client.delete_tag(tag["id"])
        results.tags_deleted += 1

    if not any(tag["resource_id"] == datasource_id for tag in tags):
        logger.info("%s: creating tag for datasource %s.", entitlement.id, datasource_id)
        if not dry_run:
            await ffc_api_client.create_tag_for_datasource(
                datasource_id=datasource_id,
                name=ENTITLEMENT_TAG_NAME,
                value=entitlement.id,
            )
        results.tags_created += 1


async def sync_organization(
    organization: Organization,
    entitlements: list[Entitlement],
    entitlement_handler: EntitlementHandler,
    optscale_client: OptscaleClient,
    ffc_api_client: FFCAPIClient,
    results: Results,
    dry_run: bool,
) -> None:
    if organization.status == OrganizationStatus.TERMINATED:
        logger.warning(
            "%s: organization is terminated but has %d active entitlements, skipping.",
            organization.id,
            len(entitlements),
        )
        results.terminated_organization_entitlements += len(entitlements)
        for entitlement in entitlements:
            results.add_error(entitlement, "Active entitlement for a terminated organization")
        return

    if organization.linked_organization_id is None:
        logger.warning(
            "%s: organization is not linked to Optscale, skipping %d entitlements.",
            organization.id,
            len(entitlements),
        )
        results.failed += len(entitlements)
        for entitlement in entitlements:
            results.add_error(entitlement, "Organization not linked to Optscale")
        return

    try:
        datasources = await fetch_datasources_by_account_id(
            optscale_client, organization.linked_organization_id
        )
        tags = await fetch_entitlement_tags(ffc_api_client, [ent.id for ent in entitlements])
    except HTTPError as exc:
        logger.warning("%s: error fetching datasources or tags: %r", organization.id, exc)
        results.failed += len(entitlements)
        for entitlement in entitlements:
            results.add_error(
                entitlement, f"Error fetching datasources or tags: {format_exception(exc)}"
            )
        return

    for entitlement in entitlements:
        datasource = datasources.get(entitlement.datasource_id)
        if datasource is None:
            logger.warning(
                "%s: datasource %s not found in organization %s.",
                entitlement.id,
                entitlement.datasource_id,
                organization.id,
            )
            results.datasources_not_found += 1
            results.add_error(entitlement, "Datasource not found in Optscale")
            continue

        old_datasource_id = entitlement.linked_datasource_id
        new_datasource_id = datasource["id"]
        relink = f"`{old_datasource_id}` → `{new_datasource_id}`"
        try:
            await sync_entitlement(
                entitlement,
                datasource,
                tags.get(entitlement.id, []),
                entitlement_handler,
                ffc_api_client,
                results,
                dry_run,
            )
        except HTTPError as exc:
            logger.warning("%s: error syncing tags: %r", entitlement.id, exc)
            results.failed += 1
            error = f"Error syncing tags: {format_exception(exc)}"
            if old_datasource_id != new_datasource_id:
                error = f"Relinked {relink}, but: {error}"
            results.add_error(entitlement, error)
            continue

        if old_datasource_id != new_datasource_id:
            results.outcomes.append(EntitlementOutcome(entitlement, relink))


@capture_telemetry_cli_command(__name__, "Sync Entitlements Datasources")
async def sync_entitlements_datasources(
    settings: Settings,
    organization_id: str | None = None,
    dry_run: bool = False,
) -> Results:
    results = Results()
    ffc_api_client = FFCAPIClient(settings)
    optscale_client = OptscaleClient(settings)

    async with session_factory() as session:
        entitlement_handler = EntitlementHandler(session)
        where_clauses = [
            Entitlement.status == EntitlementStatus.ACTIVE,
            Entitlement.redeemed_by.has(
                and_(
                    Organization.status != OrganizationStatus.DELETED,
                    Organization.deleted_at.is_(None),
                )
            ),
        ]
        if organization_id is not None:
            where_clauses.append(Entitlement.redeemed_by_id == organization_id)

        entitlements = await entitlement_handler.query_db(
            where_clauses=where_clauses,
            order_by=[Entitlement.redeemed_by_id, Entitlement.created_at],
            options=[joinedload(Entitlement.redeemed_by)],
            unique=True,
        )
        if not entitlements:
            scope = f" for organization {organization_id}" if organization_id else ""
            logger.info("No active entitlements found%s.", scope)
            return results

        by_organization: dict[str, list[Entitlement]] = defaultdict(list)
        organizations: dict[str, Organization] = {}
        for entitlement in entitlements:
            organization = cast(Organization, entitlement.redeemed_by)
            organizations[organization.id] = organization
            by_organization[organization.id].append(entitlement)

        for org_id, org_entitlements in by_organization.items():
            logger.info(
                "%s: syncing %d active entitlements.",
                org_id,
                len(org_entitlements),
            )
            await sync_organization(
                organizations[org_id],
                org_entitlements,
                entitlement_handler,
                optscale_client,
                ffc_api_client,
                results,
                dry_run,
            )
            if not dry_run:
                await session.commit()

    prefix = "Dry run: " if dry_run else ""
    logger.info(
        "%s%d entitlements relinked, %d tags created, %d orphan tags deleted, "
        "%d datasources not found, %d active entitlements for terminated organizations, "
        "%d failed.",
        prefix,
        results.relinked,
        results.tags_created,
        results.tags_deleted,
        results.datasources_not_found,
        results.terminated_organization_entitlements,
        results.failed,
    )
    if results.outcomes:
        log_outcomes(results, prefix)
        if not dry_run:
            await notify_outcomes(results)
    return results


def format_outcome_columns(outcome: EntitlementOutcome) -> tuple[str, ...]:
    ent = outcome.entitlement
    organization = cast(Organization, ent.redeemed_by)
    return (
        f"{ent.id}\t/\t{ent.name}",
        f"{ent.owner.id}\t/\t{ent.owner.name}",
        f"{organization.id}\t/\t{organization.name}",
        f"{ent.datasource_id}\t/\t{ent.linked_datasource_name}",
        outcome.details,
    )


def log_outcomes(results: Results, prefix: str) -> None:
    """Log one line per relinked entitlement and per entitlement requiring attention."""
    for outcome in results.outcomes:
        line = " | ".join(column.replace("\t", " ") for column in format_outcome_columns(outcome))
        if outcome.is_error:
            logger.warning("%sError: %s", prefix, line)
        else:
            logger.info("%sRelinked: %s", prefix, line)


async def notify_outcomes(results: Results) -> None:
    errors = sum(1 for outcome in results.outcomes if outcome.is_error)
    relinked = len(results.outcomes) - errors
    msg = (
        f"{relinked} {'entitlement has' if relinked == 1 else 'entitlements have'} been "
        f"relinked to a recreated Optscale datasource, "
        f"{errors} {'error' if errors == 1 else 'errors'} occurred."
    )
    details = NotificationDetails(
        header=(
            ColumnHeader("Entitlement", width="stretch"),
            ColumnHeader("Owner", width="stretch"),
            ColumnHeader("Organization", width="stretch"),
            ColumnHeader("Datasource", width="stretch"),
            ColumnHeader("Old → New ID / Error", width="stretch"),
        ),
        rows=[format_outcome_columns(outcome) for outcome in results.outcomes],
    )
    send = send_warning if errors else send_info
    await send(NOTIFICATION_TITLE, msg, details=details)


def command(
    ctx: typer.Context,
    organization_id: Annotated[
        str | None,
        typer.Option(
            "--organization",
            "-o",
            help="Sync only the active entitlements redeemed by this organization (FORG-...).",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Report what would change without persisting anything."),
    ] = False,
) -> None:
    """
    Sync active entitlements with their Optscale datasources: relink entitlements whose
    datasource has been recreated, delete orphan entitlement tags and create missing ones.
    """
    asyncio.run(sync_entitlements_datasources(ctx.obj, organization_id, dry_run))
