import logging
from typing import Any

from app.api_clients.mpt import MPTClient
from app.db.models import ClientAccount
from app.dependencies.db import ClientAccountRepository
from app.events.core import EventHandler, EventProcessor
from app.events.processing import ProcessingResult, ProcessingStatus

logger = logging.getLogger(__name__)


class ClientAccountProcessor(EventProcessor):
    """Keep the client accounts in sync with the marketplace client accounts."""

    object_type = "client account"

    def __init__(
        self,
        client_account_repo: ClientAccountRepository,
        account: dict[str, Any],
    ):
        self.client_account_repo = client_account_repo
        self.account = account

    @property
    def object_id(self) -> str:
        return self.account["id"]

    def completed(self, message: str, severity: str = "Info") -> ProcessingResult:
        """Log what was done to the client account and close the task."""

        logger.info("%s: %s", self.object_id, message)
        return ProcessingResult(
            status=ProcessingStatus.COMPLETE, severity=severity, message=message
        )

    async def get_client_account(self) -> ClientAccount | None:
        """Return the live client account bound to the marketplace account, by external id."""
        return await self.client_account_repo.first(
            where_clauses=[
                ClientAccount.external_id == self.object_id,
                ClientAccount.deleted_at.is_(None),
            ],
        )

    async def handle(self) -> ProcessingResult:
        client_account = await self.get_client_account()
        if client_account is None:
            return self.completed(f"The client account {self.object_id} does not exist.")

        client_account = await self.client_account_repo.update(
            client_account,
            {"name": self.account["name"], "icon": self.account.get("icon")},
        )
        return self.completed(
            f"The client account {client_account.id} was updated: "
            f"name={client_account.name!r}, icon={client_account.icon!r}."
        )


class ClientAccountEventHandler(EventHandler):
    def __init__(
        self,
        installation_client: MPTClient,
        ext_client: MPTClient,
        client_account_repo: ClientAccountRepository,
    ):
        self.installation_client = installation_client
        self.ext_client = ext_client
        self.client_account_repo = client_account_repo

    async def _get_processor(self, object_id: str) -> ClientAccountProcessor:
        account = await self.installation_client.get_account(object_id)
        return ClientAccountProcessor(
            client_account_repo=self.client_account_repo,
            account=account,
        )
