import asyncio
import logging
from dataclasses import dataclass
from typing import Annotated

import typer
from fastapi import status
from httpx import HTTPError, HTTPStatusError

from app.api_clients.mpt import MPTClient, get_installation_client
from app.conf import Settings
from app.db.base import session_factory
from app.db.handlers import AccountHandler, UserHandler
from app.db.models import Account, User
from app.enums import AccountType, UserStatus
from app.telemetry import capture_telemetry_cli_command

logger = logging.getLogger(__name__)

SYNCED_FIELDS = ("name", "email", "icon")


class OperationsAccountNotFoundError(Exception):
    pass


@dataclass
class Results:
    updated: int = 0
    unchanged: int = 0
    disabled: int = 0
    failed: int = 0


async def get_operations_client(account_repo: AccountHandler) -> MPTClient:
    operations_account = await account_repo.first(
        where_clauses=[Account.type == AccountType.OPERATIONS],
    )
    if not operations_account:
        raise OperationsAccountNotFoundError("Operations account not found.")
    return get_installation_client(operations_account.external_id)


async def start(account_repo: AccountHandler, user_repo: UserHandler) -> Results:
    results = Results()
    client = await get_operations_client(account_repo)
    users = await user_repo.query_db(
        where_clauses=[User.status == UserStatus.ACTIVE],
        order_by=[User.created_at],
    )

    for user in users:
        try:
            user_data = await client.get_user(user.external_id)
        except HTTPStatusError as e:
            if e.response.status_code != status.HTTP_404_NOT_FOUND:
                logger.warning("%s: Failed to get user %s: %s", user.id, user.external_id, e)
                results.failed += 1
                continue
            logger.info("%s: User %s not found in MPT, disabling it.", user.id, user.external_id)
            await user_repo.update(id_or_obj=user, data={"status": UserStatus.DISABLED})
            results.disabled += 1
            continue
        except HTTPError as e:
            logger.warning("%s: Failed to get user %s: %s", user.id, user.external_id, e)
            results.failed += 1
            continue

        changes = {
            field: user_data.get(field)
            for field in SYNCED_FIELDS
            if user_data.get(field) != getattr(user, field)
        }
        if not changes:
            results.unchanged += 1
            continue

        await user_repo.update(id_or_obj=user, data=changes)
        results.updated += 1

    return results


@capture_telemetry_cli_command(__name__, "Sync Users with Marketplace")
async def main(
    settings: Settings,
    dry_run: bool = False,
) -> None:
    async with session_factory() as session:
        try:
            results = await start(
                account_repo=AccountHandler(session),
                user_repo=UserHandler(session),
            )
        except OperationsAccountNotFoundError as e:
            logger.error("%s Cannot sync users.", e)
            raise typer.Exit(code=1) from e
        if dry_run:
            await session.rollback()
        else:
            await session.commit()
        report(results, dry_run)


def report(results: Results, dry_run: bool) -> None:
    prefix = "Dry run, nothing persisted. " if dry_run else ""
    logger.info(
        "%sUsers updated: %d, unchanged: %d, disabled: %d, failed: %d.",
        prefix,
        results.updated,
        results.unchanged,
        results.disabled,
        results.failed,
    )


def command(
    ctx: typer.Context,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Report what would change without persisting anything."),
    ] = False,
) -> None:
    """
    Syncs name, email and icon of the active users with the Marketplace Platform.
    Users that no longer exist in the Marketplace Platform are disabled.
    """
    logger.info("Starting command function.")

    asyncio.run(
        main(
            ctx.obj,
            dry_run,
        )
    )
    logger.info("Completed command function.")
