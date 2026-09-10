# app/commands/sync_subscriptions.py
import asyncio
import enum
import logging
from collections import Counter
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
SINCE_INPUT_FORMATS = ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]


class EntitlementAction(enum.StrEnum):
    """What syncing a subscription did, or would do, to its entitlement."""

    NONE = "none"
    CREATED = "created"
    TERMINATED = "terminated"
    DELETED = "deleted"


@dataclass
class SyncResult:
    """Outcome of syncing one subscription, aggregated for the final notification."""

    subscription_id: str
    account_id: str
    action: EntitlementAction = EntitlementAction.NONE
    message: str | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None

    @property
    def changed_entitlement(self) -> bool:
        return self.action is not EntitlementAction.NONE


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


async def load_entitlements(
    entitlement_repo: EntitlementHandler, account: Account, subscriptions: list[dict[str, Any]]
) -> dict[str, Entitlement]:
    datasource_ids = sorted({get_datasource_id(subscription) for subscription in subscriptions})
    if not datasource_ids:
        return {}

    entitlements: dict[str, Entitlement] = {}
    for entitlement in await entitlement_repo.query_db(
        where_clauses=[
            Entitlement.owner == account,
            Entitlement.datasource_id.in_(datasource_ids),
            Entitlement.status.in_([EntitlementStatus.NEW, EntitlementStatus.ACTIVE]),
        ],
        order_by=[Entitlement.created_at.desc()],
    ):
        entitlements.setdefault(entitlement.datasource_id, entitlement)
    return entitlements


def plan_action(subscription: dict[str, Any], entitlement: Entitlement | None) -> EntitlementAction:
    if subscription["status"] == ACTIVE_SUBSCRIPTION_STATUS:
        if entitlement is None:
            return EntitlementAction.CREATED
        return EntitlementAction.NONE
    else:
        if entitlement is None:
            return EntitlementAction.NONE
        if entitlement.status == EntitlementStatus.NEW:
            return EntitlementAction.DELETED
        return EntitlementAction.TERMINATED


async def sync_entitlements(
    entitlement_repo: EntitlementHandler,
    account: Account,
    subscription: dict[str, Any],
    entitlements: dict[str, Entitlement],
    dry_run: bool,
) -> tuple[EntitlementAction, str]:
    datasource_id = get_datasource_id(subscription)
    entitlement = entitlements.get(datasource_id)
    action = plan_action(subscription, entitlement)

    if action is EntitlementAction.NONE:
        if entitlement is not None:
            return action, f"The entitlement {entitlement.id} already covers the subscription."
        return action, "No live entitlement is bound to the subscription."

    if dry_run:
        subject = "An entitlement" if entitlement is None else f"The entitlement {entitlement.id}"
        return action, f"{subject} would have been {action}."

    if action is EntitlementAction.CREATED:
        created = await entitlement_repo.create(
            Entitlement(
                name=subscription["name"],
                affiliate_external_id=subscription["id"],
                datasource_id=datasource_id,
                status=EntitlementStatus.NEW,
                owner=account,
            )
        )
        entitlements[datasource_id] = created
        return action, f"The entitlement {created.id} was created."

    entitlements.pop(datasource_id, None)
    if action is EntitlementAction.DELETED:
        await entitlement_repo.delete(entitlement)
        return action, f"The entitlement {entitlement.id} was deleted."

    await entitlement_repo.terminate(entitlement)
    return action, f"The entitlement {entitlement.id} was terminated."


async def sync_subscriptions(
    subscriptions: list[dict[str, Any]], account_id: str, dry_run: bool
) -> list[SyncResult]:
    results: list[SyncResult] = []

    async with session_factory() as session:
        account = await AccountHandler(session).get(account_id)
        entitlement_repo = EntitlementHandler(session)
        entitlements = await load_entitlements(entitlement_repo, account, subscriptions)

        for subscription in subscriptions:
            action, message = await sync_entitlements(
                entitlement_repo, account, subscription, entitlements, dry_run
            )
            logger.info(f"{subscription['id']}: {message}")
            results.append(
                SyncResult(
                    subscription_id=subscription["id"],
                    account_id=account_id,
                    action=action,
                    message=message,
                )
            )

        if not dry_run:
            await session.commit()

    return results


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
    async with semaphore:
        try:
            page = await client.get_page(
                "commerce/subscriptions",
                limit=page_size,
                offset=offset,
                query=query,
                select=["id", "name", "status", "externalIds", "product", "audit"],
            )
            return await sync_subscriptions(page["data"], account_id, dry_run)
        except Exception as exc:
            logger.exception(f"{account_id}: failed to sync the page at offset {offset}")
            page_id = f"offset {offset}"
            return [SyncResult(subscription_id=page_id, account_id=account_id, error=str(exc))]


async def count_subscriptions(client: MPTClient, query: str) -> int:
    page = await client.get_page("commerce/subscriptions", limit=1, offset=0, query=query)
    return page["$meta"]["pagination"]["total"]


async def sync_account(
    account: Account,
    since: datetime,
    until: datetime,
    settings: Settings,
    dry_run: bool,
    semaphore: asyncio.Semaphore,
) -> list[SyncResult]:
    client: MPTClient = get_installation_client(account.external_id)
    query = build_query(account_products(account), since, until)
    total = await count_subscriptions(client, query)
    if not total:
        logger.info(f"{account.id}: no subscription changed inside the window")
        return []

    page_size = settings.subscriptions_sync_page_size
    logger.info(f"{account.id}: syncing {total} subscriptions")
    tasks = [
        asyncio.create_task(
            sync_page(client, query, offset, page_size, account.id, dry_run, semaphore)
        )
        for offset in range(0, total, page_size)
    ]
    return [result for page_results in await asyncio.gather(*tasks) for result in page_results]


def build_notification_details(results: list[SyncResult]) -> NotificationDetails:
    header = (
        ColumnHeader(text="Account", width="90px"),
        ColumnHeader(text="Subscription", width="120px"),
        ColumnHeader(text="Action"),
        ColumnHeader(text="Details"),
    )
    rows = [
        (
            result.account_id,
            result.subscription_id,
            "failed" if not result.succeeded else result.action.value,
            result.error or result.message or "",
        )
        for result in results
        if not result.succeeded or result.changed_entitlement
    ]
    return NotificationDetails(header=header, rows=rows)


async def report(results: list[SyncResult], since: datetime, until: datetime) -> None:
    window = (
        f"changed between {since.strftime(MPT_DATETIME_FORMAT)} "
        f"and {until.strftime(MPT_DATETIME_FORMAT)}"
    )
    failed = [result for result in results if not result.succeeded]
    changed = [result for result in results if result.succeeded and result.changed_entitlement]
    actions = ", ".join(
        f"{action}: {count}"
        for action, count in sorted(Counter(result.action.value for result in changed).items())
    )

    if failed:
        text = (
            f"Checked {len(results)} subscriptions {window}. "
            f"{len(failed)} failed to sync, {len(changed)} entitlements changed"
            f"{f' ({actions})' if actions else ''}."
        )
        logger.warning(text)
        await send_error(
            "Subscriptions Sync Partial Failure", text, details=build_notification_details(results)
        )
        return

    if changed:
        text = (
            f"Checked {len(results)} subscriptions {window} and brought "
            f"{len(changed)} entitlements back in sync ({actions})."
        )
        logger.info(text)
        await send_info(
            "Subscriptions Sync Applied Changes",
            text,
            details=build_notification_details(changed),
        )
        return

    text = (
        f"Checked {len(results)} subscriptions {window}: every entitlement was already in sync."
    )
    logger.info(text)
    await send_info("Subscriptions Sync Success", text)


@capture_telemetry_cli_command(__name__, "Sync Subscriptions")
async def main(
    settings: Settings,
    account_external_id: str | None = None,
    since: datetime | None = None,
    dry_run: bool = False,
) -> None:
    until = datetime.now(UTC)
    if since is None:
        since = until - timedelta(hours=settings.subscriptions_sync_lookback_hours)
    elif since.tzinfo is None:
        since = since.replace(tzinfo=UTC)
    semaphore = asyncio.Semaphore(settings.subscriptions_sync_max_parallel)

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
        f"Syncing the subscriptions of {len(accounts)} affiliate accounts "
        f"changed between {since.isoformat()} and {until.isoformat()}"
    )

    results: list[SyncResult] = []
    for account in accounts:
        try:
            results.extend(await sync_account(account, since, until, settings, dry_run, semaphore))
        except Exception as exc:
            logger.exception(f"Failed to sync the subscriptions of account {account.id}")
            results.append(SyncResult(subscription_id="n/a", account_id=account.id, error=str(exc)))

    if not dry_run:
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
            formats=SINCE_INPUT_FORMATS,
            help="Sync the subscriptions changed after this UTC date or datetime. "
            "Default: the start of this run minus the configured interval",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Report what would change without writing anything"),
    ] = False,
) -> None:
    """
    Sync the entitlements with the marketplace subscriptions.

    Applies the same rules as the subscription event flow, for events that were missed.
    """
    logger.info("Starting command function")
    asyncio.run(main(ctx.obj, account, since, dry_run))
    logger.info("Completed command function")
