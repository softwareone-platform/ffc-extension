from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import httpx
import pytest
from httpx import Response
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_clients.mpt import MPTClient
from app.conf import Settings
from app.db.handlers import ClientAccountHandler
from app.db.models import ClientAccount
from app.events.accounts.processing import ClientAccountEventHandler, ClientAccountProcessor
from app.events.exceptions import HandlerHTTPError
from app.events.processing import ProcessingStatus
from app.schemas.core import Event, ExtensionContext
from tests.types import EventFactory, ModelFactory, MPTAccountFactory, MPTAccountMocker

ACCOUNT_ID = "ACC-4444-4444"


# -- get_processor --


async def test_get_processor_for_client_account_event(
    client_account_event_handler: ClientAccountEventHandler,
    mpt_account_factory: MPTAccountFactory,
    mock_get_account: MPTAccountMocker,
    db_session: AsyncSession,
) -> None:
    """`get_processor` fetches the account and hands it to the processor."""
    account = mpt_account_factory()
    mock_get_account(account)

    processor = await client_account_event_handler.get_processor(object_id=ACCOUNT_ID)

    assert isinstance(processor, ClientAccountProcessor)
    assert processor.account == account
    assert processor.object_id == ACCOUNT_ID
    assert processor.client_account_repo.session is db_session


async def test_get_processor_propagates_a_marketplace_failure(
    client_account_event_handler: ClientAccountEventHandler,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
) -> None:
    """A marketplace error is not a domain error: the platform retries the event."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/accounts/accounts/{ACCOUNT_ID}",
        status_code=httpx.codes.NOT_FOUND,
        json={"errors": {"id": "Account not found"}},
    )

    with pytest.raises(HandlerHTTPError, match=ACCOUNT_ID) as exc_info:
        await client_account_event_handler.get_processor(object_id=ACCOUNT_ID)

    result = exc_info.value.to_result()
    assert result.status is ProcessingStatus.RESCHEDULE
    assert result.severity == "Error"


# -- process --


async def test_process_updates_the_name_and_icon_of_the_client_account(
    mpt_account_factory: MPTAccountFactory,
    client_account_factory: ModelFactory[ClientAccount],
    db_session: AsyncSession,
) -> None:
    """An existing client account takes the marketplace name and icon, and the task is closed."""
    client_account = await client_account_factory(
        name="Old name", icon="/old/icon", external_id=ACCOUNT_ID
    )
    processor = ClientAccountProcessor(
        client_account_repo=ClientAccountHandler(db_session),
        account=mpt_account_factory(name="New name", icon="/new/icon"),
    )

    result = await processor.process()

    await db_session.refresh(client_account)
    assert client_account.name == "New name"
    assert client_account.icon == "/new/icon"
    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Info"
    assert result.message == (
        f"The client account {client_account.id} was updated: name='New name', icon='/new/icon'."
    )


async def test_process_clears_the_icon_when_the_account_has_none(
    mpt_account_factory: MPTAccountFactory,
    client_account_factory: ModelFactory[ClientAccount],
    db_session: AsyncSession,
) -> None:
    """An account without an icon clears the icon of the client account."""
    client_account = await client_account_factory(icon="/old/icon", external_id=ACCOUNT_ID)
    processor = ClientAccountProcessor(
        client_account_repo=ClientAccountHandler(db_session),
        account=mpt_account_factory(icon=None),
    )

    await processor.process()

    await db_session.refresh(client_account)
    assert client_account.icon is None


async def test_process_completes_when_the_client_account_does_not_exist(
    mpt_account_factory: MPTAccountFactory,
    db_session: AsyncSession,
) -> None:
    """An account with no client account is logged and the task is closed."""
    processor = ClientAccountProcessor(
        client_account_repo=ClientAccountHandler(db_session),
        account=mpt_account_factory(),
    )

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Info"
    assert result.message == f"The client account {ACCOUNT_ID} does not exist."


async def test_process_ignores_a_deleted_client_account(
    mpt_account_factory: MPTAccountFactory,
    client_account_factory: ModelFactory[ClientAccount],
    db_session: AsyncSession,
) -> None:
    """A soft-deleted client account is not updated: it is reported as missing."""
    client_account = await client_account_factory(
        name="Old name", external_id=ACCOUNT_ID, deleted_at=datetime.now(UTC)
    )
    processor = ClientAccountProcessor(
        client_account_repo=ClientAccountHandler(db_session),
        account=mpt_account_factory(name="New name"),
    )

    result = await processor.process()

    await db_session.refresh(client_account)
    assert client_account.name == "Old name"
    assert result.message == f"The client account {ACCOUNT_ID} does not exist."


# -- endpoint --


async def test_process_client_account_updates_and_completes_the_task(
    mocker: MockerFixture,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_client_account_event: Callable[[Event], Awaitable[Response]],
    mpt_account_factory: MPTAccountFactory,
    client_account_factory: ModelFactory[ClientAccount],
    db_session: AsyncSession,
) -> None:
    """A client account event refreshes the client account and closes its task."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    client_account = await client_account_factory(name="Old name", external_id=ACCOUNT_ID)
    account = mpt_account_factory(name="New name", icon="/new/icon")
    event = event_factory(object_id=ACCOUNT_ID, object_name="account", object_type="Account")
    mocked_start_task = mocker.patch.object(MPTClient, "start_task")
    mocked_get_account = mocker.patch.object(MPTClient, "get_account", return_value=account)
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await post_client_account_event(event)

    assert response.status_code == 200
    assert response.json()["response"] == "OK"
    await db_session.refresh(client_account)
    assert client_account.name == "New name"
    assert client_account.icon == "/new/icon"
    mocked_start_task.assert_awaited_once_with(event.task.id, mocked_extension_ctx.instance_id)
    mocked_get_account.assert_awaited_once_with(ACCOUNT_ID)
    mocked_log_task.assert_awaited_once_with(
        event.task.id,
        severity="Info",
        error_message=(
            f"The client account {client_account.id} was updated: "
            "name='New name', icon='/new/icon'."
        ),
    )
    mocked_complete_task.assert_awaited_once_with(event.task.id)


async def test_process_client_account_completes_the_task_for_an_unknown_client_account(
    mocker: MockerFixture,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_client_account_event: Callable[[Event], Awaitable[Response]],
    mpt_account_factory: MPTAccountFactory,
) -> None:
    """An event for an account with no client account is logged and its task closed."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(object_id=ACCOUNT_ID, object_name="account", object_type="Account")
    mocker.patch.object(MPTClient, "start_task")
    mocker.patch.object(MPTClient, "get_account", return_value=mpt_account_factory())
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await post_client_account_event(event)

    assert response.status_code == 200
    assert response.json()["response"] == "OK"
    mocked_log_task.assert_awaited_once_with(
        event.task.id,
        severity="Info",
        error_message=f"The client account {ACCOUNT_ID} does not exist.",
    )
    mocked_complete_task.assert_awaited_once_with(event.task.id)
