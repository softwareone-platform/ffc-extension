import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import httpx
import typer

from app.api_clients.optscale import OptscaleClient
from app.conf import Settings
from app.db.base import session_factory
from app.db.handlers import OrganizationHandler
from app.db.models import Organization
from app.enums import OrganizationStatus
from app.notifications import NotificationDetails, send_info, send_warning
from app.telemetry import capture_telemetry_cli_command
from app.utils import get_organization_terminated_before

logger = logging.getLogger(__name__)

RESULT_DELETED = "✅"  # ✅
RESULT_FAILED = "❌"  # ❌
MAX_ERROR_LENGTH = 200

NOTIFICATION_HEADER = (
    "Organization ID",
    "Operations external ID",
    "Client account external ID",
    "Termination date",
    "Result",
)


@dataclass
class DeletionResult:
    organization_id: str
    linked_organization_id: str | None
    operations_external_id: str
    client_account_external_id: str
    termination_date: date
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None

    def to_row(self) -> tuple[str, ...]:
        result = RESULT_DELETED if self.succeeded else f"{RESULT_FAILED} {self.error}"
        return (
            self.organization_id,
            self.operations_external_id,
            self.client_account_external_id,
            self.termination_date.isoformat(),
            result,
        )


def short_error(exc: Exception) -> str:
    message = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
    if len(message) > MAX_ERROR_LENGTH:
        message = f"{message[: MAX_ERROR_LENGTH - 1]}…"
    return message


async def delete_organization(result: DeletionResult, optscale_client: OptscaleClient) -> None:
    # Each organization is deleted in its own session and transaction, so a failure
    # only rolls back the organization being processed.
    async with session_factory() as session, session.begin():
        organization_handler = OrganizationHandler(session)
        organization = await organization_handler.get(
            result.organization_id,
            extra_conditions=[Organization.status == OrganizationStatus.TERMINATED],
        )
        if result.linked_organization_id:
            try:
                await optscale_client.delete_organization(
                    organization_id=result.linked_organization_id,
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code != httpx.codes.NOT_FOUND:
                    raise
                logger.warning(
                    "Linked organization %s of organization %s not found in Optscale, "
                    "deleting it only from the database",
                    result.linked_organization_id,
                    result.organization_id,
                )
        else:
            logger.warning(
                "Organization %s has no linked organization ID, deleting it only from the database",
                result.organization_id,
            )
        await organization_handler.delete(organization)


@capture_telemetry_cli_command(__name__, "Delete Terminated Organizations")
async def main(settings: Settings) -> None:
    now = datetime.now(UTC)
    grace_days = settings.organization_deletion_grace_period_days

    # An organization is deletable by the job once deletable_at + grace period has passed,
    # i.e. when deletable_at <= now - grace period.
    terminated_before = get_organization_terminated_before(now - timedelta(days=grace_days))

    async with session_factory() as session:
        logger.info(
            "Fetching organizations terminated before %s from the database",
            terminated_before.isoformat(),
        )
        organizations = await OrganizationHandler(session).query_db(
            where_clauses=[
                Organization.status == OrganizationStatus.TERMINATED,
                Organization.terminated_at < terminated_before,
            ],
            order_by=[Organization.terminated_at],
        )
        results = [
            DeletionResult(
                organization_id=org.id,
                linked_organization_id=org.linked_organization_id,
                operations_external_id=org.operations_external_id,
                client_account_external_id=(
                    org.client_account.external_id if org.client_account else "-"
                ),
                termination_date=org.terminated_at.astimezone(UTC).date(),  # ty: ignore[unresolved-attribute]
            )
            for org in organizations
        ]

    logger.info(
        "Found %d terminated organizations past their %d days grace period",
        len(results),
        grace_days,
    )

    if not results:
        logger.info("No terminated organizations to delete")
        return

    async with OptscaleClient(settings) as optscale_client:
        for result in results:
            try:
                await delete_organization(result, optscale_client)
                logger.info("Organization %s has been deleted", result.organization_id)
            except Exception as exc:
                logger.exception("Failed to delete organization %s", result.organization_id)
                result.error = short_error(exc)

    failed = [r for r in results if not r.succeeded]
    title = "Delete Terminated Organizations"
    text = (
        f"{len(results) - len(failed)} of {len(results)} terminated organizations "
        f"past their {grace_days} days grace period have been deleted."
    )
    logger.info(text)
    details = NotificationDetails(header=NOTIFICATION_HEADER, rows=[r.to_row() for r in results])
    if failed:
        await send_warning(title, text, details=details)
    else:
        await send_info(title, text, details=details)


def command(ctx: typer.Context) -> None:
    """
    Delete terminated organizations whose deletable date plus the configured
    grace period has passed.
    """
    asyncio.run(main(ctx.obj))
