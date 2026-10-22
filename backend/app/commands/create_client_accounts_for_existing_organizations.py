import asyncio
import logging
from dataclasses import dataclass
from typing import Annotated

import typer
from httpx import HTTPError

from app.api_clients.mpt import MPTClient, get_installation_client
from app.conf import Settings
from app.db.base import session_factory
from app.db.handlers import ClientAccountHandler, OrganizationHandler
from app.db.models import Organization
from app.schemas.core import ExtensionContext
from app.telemetry import capture_telemetry_cli_command

logger = logging.getLogger(__name__)


@dataclass
class Results:
    created: int = 0
    linked: int = 0
    failed: int = 0


async def start(
    organization_repo: OrganizationHandler,
    client_account_repo: ClientAccountHandler,
) -> Results:
    results = Results()
    client_accounts_ids: dict[str, str] = {}
    ext_ctx = ExtensionContext.from_identity_file()
    client: MPTClient = get_installation_client(ext_ctx.account_id)
    organizations = await organization_repo.query_db(
        where_clauses=[Organization.client_account_id.is_(None)],
        order_by=[Organization.created_at],
    )

    for organization in organizations:
        agreement_id = organization.operations_external_id
        # fetch the agreement from MPT
        try:
            agreement = await client.get_agreement(agreement_id)
        except HTTPError:
            logger.warning("%s: Failed to get agreement for %s", organization.id, agreement_id)
            results.failed += 1
            continue

        agreement_client = agreement["client"]
        client_id = agreement_client["id"]
        if client_id in client_accounts_ids:
            client_account_id = client_accounts_ids[client_id]
        else:
            client_account, created = await client_account_repo.update_or_create(
                external_id=client_id,
                defaults={"name": agreement_client["name"], "icon": agreement_client.get("icon")},
            )
            if created:
                results.created += 1
            # update the map
            client_accounts_ids[client_id] = client_account.id
            client_account_id = client_account.id
        # update the organization's client_account to the client_account_id
        await organization_repo.update(
            id_or_obj=organization, data={"client_account_id": client_account_id}
        )
        results.linked += 1
    return results


@capture_telemetry_cli_command(__name__, "Create Client Accounts for Existing Organizations")
async def main(
    settings: Settings,
    dry_run: bool = False,
) -> None:
    async with session_factory() as session:
        results = await start(
            organization_repo=OrganizationHandler(session),
            client_account_repo=ClientAccountHandler(session),
        )
        if dry_run:
            await session.rollback()
        else:
            await session.commit()
        report(results, dry_run)


def report(results: Results, dry_run: bool) -> None:
    if dry_run:
        logger.info(
            "Dry run: %d client accounts would be created, %d organizations would be linked and "
            "%d failed.",
            results.created,
            results.linked,
            results.failed,
        )
    else:
        logger.info(
            "%d Client accounts created, %d organizations linked and %d failed.",
            results.created,
            results.linked,
            results.failed,
        )


def command(
    ctx: typer.Context,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Nothing will be persisted"),
    ] = False,
) -> None:
    logger.info("Starting command function.")

    asyncio.run(
        main(
            ctx.obj,
            dry_run,
        )
    )
    logger.info("Completed command function.")
