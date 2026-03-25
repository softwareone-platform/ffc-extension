import asyncio
import logging
from datetime import UTC, datetime

import typer
from sqlalchemy import select, update

from app.conf import Settings
from app.db.base import session_factory
from app.db.models import Account, AccountUser, User
from app.enums import AccountUserStatus
from app.notifications import NotificationDetails, send_info
from app.telemetry import capture_telemetry_cli_command

logger = logging.getLogger(__name__)


@capture_telemetry_cli_command(__name__, "Check Expired Invitations")
async def check_expired_invitations(settings: Settings):
    async with session_factory.begin() as session:
        stmt = (
            update(AccountUser)
            .where(
                AccountUser.status == AccountUserStatus.INVITED,
                AccountUser.invitation_token_expires_at < datetime.now(UTC),
            )
            .values(status=AccountUserStatus.INVITATION_EXPIRED)
            .returning(AccountUser.id)
        )

        result = await session.execute(stmt)
        accountuser_ids = [row[0] for row in result.fetchall()]
        expired_count = len(accountuser_ids)
        message = "Invitation has" if expired_count == 1 else "Invitations have"
        message = (
            f"{expired_count} {message} been successfully transitioned to `invitation-expired`."
        )

        logger.info(message)
        if expired_count > 0:
            user_query = (
                select(
                    User.id,
                    User.name,
                    User.email,
                    Account.id.label("account_id"),
                    Account.name.label("account_name"),
                )
                .join(AccountUser, AccountUser.user_id == User.id)
                .join(Account, AccountUser.account_id == Account.id)
                .where(AccountUser.id.in_(accountuser_ids))
                .order_by(User.name, Account.name)
            )
            user_result = await session.execute(user_query)
            users = user_result.all()
            await send_info(
                "Expire Invitations Success",
                message,
                details=NotificationDetails(
                    header=("User ID", "Name", "Email", "Account ID", "Account Name"),
                    rows=[
                        (
                            user.id,
                            user.name,
                            user.email,
                            user.account_id,
                            user.account_name,
                        )
                        for user in users
                    ],
                ),
            )


def command(ctx: typer.Context):
    """Transition expired invitations to the `invitation-expired` status."""
    asyncio.run(check_expired_invitations(ctx.obj))
