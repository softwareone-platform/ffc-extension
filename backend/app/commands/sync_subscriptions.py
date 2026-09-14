import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import typer

from app.api_clients.mpt import MPTClient, get_installation_client
from app.conf import Settings
from app.db.base import session_factory
from app.db.handlers import AccountHandler, EntitlementHandler
from app.db.models import Account, Entitlement
from app.enums import AccountStatus, AccountType, EntitlementStatus
from app.events.subscriptions.constants import (
    ACTIVE_SUBSCRIPTION_STATUS,
    TERMINATED_SUBSCRIPTION_STATUS,
)
from app.events.subscriptions.utils import get_datasource_id
from app.notifications import ColumnHeader, NotificationDetails, send_error, send_info
from app.telemetry import capture_telemetry_cli_command

logger = logging.getLogger(__name__)

MPT_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.000Z"
TIMEFRAME_INPUT_FORMATS = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]
READABLE_DT_FORMAT = "%Y-%m-%d %H:%M:%S UTC"


@dataclass
class SyncResult:
    """Outcome of syncing one subscription, aggregated for the final notification."""

    account_id: str
    message: str
    subscription_id: str | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


def account_products(account: Account) -> list[str]:
    return sorted({product.strip() for product in account.products.split(",") if product.strip()})


def build_query(products: list[str], since: datetime, until: datetime) -> str:
    lower = since.strftime(MPT_DATETIME_FORMAT)
    upper = until.strftime(MPT_DATETIME_FORMAT)
    window = ",".join(
        f"and(gt({field},{lower}),lt({field},{upper}))"
        for field in ("audit.created.at", "audit.updated.at")
    )
    conditions = [
        f"in(product.id,({','.join(products)}))",
        f"in(status,({','.join([ACTIVE_SUBSCRIPTION_STATUS, TERMINATED_SUBSCRIPTION_STATUS])}))",
        f"or({window})",
    ]
    return f"and({','.join(conditions)})"


async def sync_subscription(
    entitlement_handler: EntitlementHandler,
    account: Account,
    subscription: dict[str, Any],
    entitlements: list[Entitlement],
) -> SyncResult | None:
    sub_id = subscription["id"]

    if subscription["status"] == ACTIVE_SUBSCRIPTION_STATUS:
        if len(entitlements) > 1:
            entitlement_ids = ", ".join([entitlement.id for entitlement in entitlements])
            logger.warning(
                f"Subscription {sub_id} has more than one new and/or "
                f"active entitlement: {entitlement_ids}"
            )
            return SyncResult(
                subscription_id=sub_id,
                account_id=account.id,
                message=f"Found active and new entitlements: {entitlement_ids}.",
                error="Subscription has more than one new and/or active entitlement.",
            )
        if len(entitlements) == 0:
            created = await entitlement_handler.create(
                Entitlement(
                    name=subscription["name"],
                    affiliate_external_id=sub_id,
                    datasource_id=get_datasource_id(subscription),
                    status=EntitlementStatus.NEW,
                    owner=account,
                )
            )
            logger.info(f"Created entitlement {created.id} for subscription {sub_id}.")
            return SyncResult(
                subscription_id=sub_id,
                account_id=account.id,
                message=f"Created new entitlement {created.id}.",
            )
    else:
        if entitlements:
            actions = []
            for entitlement in entitlements:
                if entitlement.status == EntitlementStatus.NEW:
                    await entitlement_handler.delete(entitlement)
                    actions.append(f"The entitlement {entitlement.id} was deleted.")
                    logger.info(f"Deleted entitlement {entitlement.id} for subscription {sub_id}.")
                else:
                    await entitlement_handler.terminate(entitlement)
                    actions.append(f"The entitlement {entitlement.id} was terminated.")
                    logger.info(
                        f"Terminated entitlement {entitlement.id} for subscription {sub_id}."
                    )
            return SyncResult(
                subscription_id=sub_id,
                account_id=account.id,
                message="\n".join(actions),
            )

    logger.info(f"Subscription {sub_id} is already synced.")
    return None


async def sync_page(
    client: MPTClient,
    query: str,
    offset: int,
    page_size: int,
    account_id: str,
    dry_run: bool,
    semaphore: asyncio.Semaphore,
) -> list[SyncResult]:
    """Fetch one page of subscriptions and sync it."""
    results: list[SyncResult] = []
    async with semaphore:
        try:
            page = await client.get_page(
                "commerce/subscriptions",
                limit=page_size,
                offset=offset,
                query=query,
                select=["id", "name", "status", "externalIds"],
            )
            subscriptions = page["data"]

            async with session_factory() as session:
                account = await AccountHandler(session).get(account_id)
                entitlement_handler = EntitlementHandler(session)

                for subscription in subscriptions:
                    entitlements = await entitlement_handler.query_db(
                        where_clauses=[
                            Entitlement.owner == account,
                            Entitlement.datasource_id == get_datasource_id(subscription),
                            Entitlement.status.in_(
                                [EntitlementStatus.NEW, EntitlementStatus.ACTIVE]
                            ),
                        ],
                    )
                    result = await sync_subscription(
                        entitlement_handler,
                        account,
                        subscription,
                        entitlements,
                    )
                    if result:
                        results.append(result)

                    if dry_run:
                        await session.rollback()
                    else:
                        await session.commit()

            return results
        except Exception as exc:
            msg = f"{account_id}: failed to sync the page with {offset=}."
            logger.exception(msg)
            return [
                *results,
                SyncResult(
                    account_id=account_id,
                    error=str(exc),
                    message=msg,
                ),
            ]


async def sync_account(
    account: Account,
    since: datetime,
    until: datetime,
    page_size: int,
    dry_run: bool,
    semaphore: asyncio.Semaphore,
) -> list[SyncResult]:
    client: MPTClient = get_installation_client(account.external_id)
    query = build_query(account_products(account), since, until)
    total = await client.count("commerce/subscriptions", query)
    if not total:
        logger.info(f"{account.id}: no subscription events within the window. Skip it.")
        return []

    logger.info(f"{account.id}: syncing {total} subscriptions")
    tasks = [
        asyncio.create_task(
            sync_page(client, query, offset, page_size, account.id, dry_run, semaphore)
        )
        for offset in range(0, total, page_size)
    ]
    results = [result for page_results in await asyncio.gather(*tasks) for result in page_results]
    return results


def build_notification_details(results: list[SyncResult]) -> NotificationDetails:
    header = (
        ColumnHeader(text="Account", width="stretch"),
        ColumnHeader(text="Subscription", width="stretch"),
        ColumnHeader(text="Action", width="stretch"),
        ColumnHeader(text="Details", width="stretch"),
    )
    rows = [
        (
            result.account_id,
            result.subscription_id or "",
            result.message,
            result.error or "",
        )
        for result in results
    ]
    return NotificationDetails(header=header, rows=rows)


async def report(results: list[SyncResult], since: datetime, until: datetime) -> None:
    window = (
        f"changed between {since.strftime(READABLE_DT_FORMAT)} and "
        f"{until.strftime(READABLE_DT_FORMAT)}"
    )

    if len(results) == 0:
        text = f"Checked subscriptions {window}: all in sync."
        logger.info(text)
        await send_info("Subscriptions Sync Success", text)
        return

    failed = [result for result in results if not result.succeeded]
    if failed:
        text = f"Checked subscriptions {window}. Partially failed to sync."
        logger.warning(text)
        await send_error(
            "Subscriptions Sync Partial Failure", text, details=build_notification_details(results)
        )
        return

    text = f"Checked subscriptions {window} and synced {len(results)} subscriptions."
    logger.info(text)
    await send_info(
        "Subscriptions Sync Applied Changes",
        text,
        details=build_notification_details(results),
    )
    return


@capture_telemetry_cli_command(__name__, "Sync Subscriptions")
async def main(
    settings: Settings,
    page_size: int,
    max_parallel: int,
    lookback_hours: int,
    account_external_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    dry_run: bool = False,
) -> None:
    until = until or datetime.now(UTC)
    if until.tzinfo is None:
        until = until.replace(tzinfo=UTC)
    since = since or until - timedelta(hours=lookback_hours)
    if since.tzinfo is None:
        since = since.replace(tzinfo=UTC)

    semaphore = asyncio.Semaphore(max_parallel)

    async with session_factory() as session:
        where_clauses = [
            Account.type == AccountType.AFFILIATE,
            Account.status == AccountStatus.ACTIVE,
            Account.products.is_not(None),
            Account.products != "",
        ]
        if account_external_id:
            where_clauses.append(Account.external_id == account_external_id)
        accounts = await AccountHandler(session).query_db(where_clauses=where_clauses)

    logger.info(
        f"Syncing subscriptions of {len(accounts)} affiliate accounts created or changed between "
        f"{since.strftime(READABLE_DT_FORMAT)} and {until.strftime(READABLE_DT_FORMAT)}"
    )

    results: list[SyncResult] = []
    for account in accounts:
        try:
            results.extend(await sync_account(account, since, until, page_size, dry_run, semaphore))
        except Exception as exc:
            logger.exception(f"Failed to sync the subscriptions for account {account.id}: {exc}")
            results.append(
                SyncResult(
                    account_id=account.id,
                    message=f"Failed to sync the subscriptions of account {account.id}",
                    error=str(exc),
                )
            )

    if dry_run:
        logger.info(results)
    else:
        await report(results, since, until)


def command(
    ctx: typer.Context,
    account: Annotated[
        str | None,
        typer.Option(
            "--account",
            "-a",
            help="Affiliate account external ID. Default: every active affiliate account",
        ),
    ] = None,
    since: Annotated[
        datetime | None,
        typer.Option(
            "--since",
            "-s",
            formats=TIMEFRAME_INPUT_FORMATS,
            help="Sync the subscriptions changed after this UTC date or datetime. "
            "Default: the start of command run minus the configured interval",
        ),
    ] = None,
    until: Annotated[
        datetime | None,
        typer.Option(
            "--until",
            "-u",
            formats=TIMEFRAME_INPUT_FORMATS,
            help="Sync the subscriptions changed before this UTC date or datetime. "
            "Default: the start of command run",
        ),
    ] = None,
    page_size: Annotated[
        int,
        typer.Option(
            "--page-size",
            help="Amount of subscription fetched at once to process",
        ),
    ] = 50,
    max_parallel: Annotated[
        int,
        typer.Option(
            "--max-parallel",
            help="Number of processes that can run in parallel",
        ),
    ] = 5,
    lookback_hours: Annotated[
        int,
        typer.Option(
            "--lookback-hours",
            help="Define the window in hours to filter subscriptions creation or update. "
            "Will be ignored if since argument is passed",
        ),
    ] = 24,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Test what needs a change"),
    ] = False,
) -> None:
    """
    Sync the entitlements with the marketplace subscriptions.

    Applies the same rules as the subscription event flow, for events that were missed.
    """
    logger.info("Starting command function")
    asyncio.run(
        main(ctx.obj, page_size, max_parallel, lookback_hours, account, since, until, dry_run)
    )
    logger.info("Completed command function")
