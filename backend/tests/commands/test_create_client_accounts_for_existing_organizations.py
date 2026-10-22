import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner

from app.cli import app
from app.commands import create_client_accounts_for_existing_organizations
from app.conf import Settings
from app.db.models import ClientAccount, Organization
from tests.types import ModelFactory

pytestmark = pytest.mark.usefixtures("mock_installation_client")


async def test_main_creates_client_account_and_links_organization(
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An organization whose client is unknown gets a new client account built from the
    agreement's client and is linked to it."""
    organization = await organization_factory(operations_external_id="AGR-0001")
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/AGR-0001",
        status_code=200,
        json={
            "id": "AGR-0001",
            "name": "Good Deals Inc",
            "client": {
                "id": "ACC-1000-0001",
                "name": "Client 01",
                "icon": "/v1/accounts/accounts/ACC-0001-0001/icon",
            },
        },
    )
    with caplog.at_level("INFO"):
        await create_client_accounts_for_existing_organizations.main(test_settings)

    await db_session.refresh(organization)
    client_account = organization.client_account
    assert client_account is not None
    assert client_account.external_id == "ACC-1000-0001"
    assert client_account.name == "Client 01"
    assert client_account.icon == "/v1/accounts/accounts/ACC-0001-0001/icon"
    assert "1 Client accounts created, 1 organizations linked and 0 failed." in caplog.text


async def test_main_links_organization_to_existing_client_account(
    test_settings: Settings,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
    organization_factory: ModelFactory[Organization],
    client_account_factory: ModelFactory[ClientAccount],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A client account that already exists for the agreement's client is reused and its
    name and icon are refreshed; no second row is created."""
    existing = await client_account_factory(
        external_id="ACC-1000-0002", name="Old name", icon="/old.png"
    )
    organization = await organization_factory(operations_external_id="AGR-0002")
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/AGR-0002",
        status_code=200,
        json={
            "id": "AGR-0002",
            "name": "Good Deals Inc",
            "client": {
                "id": "ACC-1000-0002",
                "name": "Client 02",
                "icon": "/v1/accounts/accounts/ACC-0001-0002/icon",
            },
        },
    )

    with caplog.at_level("INFO"):
        await create_client_accounts_for_existing_organizations.main(test_settings)

    await db_session.refresh(organization)
    await db_session.refresh(existing)
    assert organization.client_account_id == existing.id
    assert existing.name == "Client 02"
    assert existing.icon == "/v1/accounts/accounts/ACC-0001-0002/icon"
    assert await db_session.scalar(select(func.count()).select_from(ClientAccount)) == 1
    assert "0 Client accounts created, 1 organizations linked and 0 failed." in caplog.text


async def test_main_reuses_client_account_for_organizations_sharing_a_client(
    test_settings: Settings,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
    organization_factory: ModelFactory[Organization],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Organizations whose agreements share a client are linked to one client account.
    The client is looked up once: the second agreement's client details are never applied."""
    first = await organization_factory(operations_external_id="AGR-0003")
    second = await organization_factory(operations_external_id="AGR-0004")
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/AGR-0003",
        status_code=200,
        json={
            "id": "AGR-0003",
            "client": {
                "id": "ACC-1000-0003",
                "name": "Name from AGR-0003",
                "icon": "/v1/accounts/accounts/ACC-0001-0003/icon3",
            },
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/AGR-0004",
        status_code=200,
        json={
            "id": "AGR-0004",
            "client": {
                "id": "ACC-1000-0003",
                "name": "Name from AGR-0003",
                "icon": "/v1/accounts/accounts/ACC-0001-0003/icon3",
            },
        },
    )

    with caplog.at_level("INFO"):
        await create_client_accounts_for_existing_organizations.main(test_settings)

    await db_session.refresh(first)
    await db_session.refresh(second)
    assert first.client_account is not None
    assert first.client_account_id == second.client_account_id
    assert first.client_account.name == "Name from AGR-0003"
    assert first.client_account.icon == "/v1/accounts/accounts/ACC-0001-0003/icon3"
    assert await db_session.scalar(select(func.count()).select_from(ClientAccount)) == 1
    assert "1 Client accounts created, 2 organizations linked and 0 failed." in caplog.text


async def test_main_skips_organizations_already_linked(
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    client_account_factory: ModelFactory[ClientAccount],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An organization that already has a client account is neither fetched from the
    marketplace nor touched."""
    client_account = await client_account_factory(external_id="ACC-1000-0005")
    organization = await organization_factory(
        operations_external_id="AGR-0005", client_account=client_account
    )

    with caplog.at_level("INFO"):
        await create_client_accounts_for_existing_organizations.main(test_settings)

    await db_session.refresh(organization)
    assert organization.client_account_id == client_account.id
    assert await db_session.scalar(select(func.count()).select_from(ClientAccount)) == 1
    assert "0 Client accounts created, 0 organizations linked and 0 failed." in caplog.text


async def test_main_second_run_changes_nothing(
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Running the command twice links every organization once and creates no duplicate
    client account; the second run has nothing to do."""
    organization = await organization_factory(operations_external_id="AGR-0006")
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/AGR-0006",
        status_code=200,
        json={
            "id": "AGR-0006",
            "name": "Good Deals Inc",
            "client": {
                "id": "ACC-1000-0006",
                "name": "Client 06",
                "icon": "/v1/accounts/accounts/ACC-0001-0001/icon",
            },
        },
    )
    with caplog.at_level("INFO"):
        await create_client_accounts_for_existing_organizations.main(test_settings)

    await db_session.refresh(organization)
    linked_to = organization.client_account_id
    assert "1 Client accounts created, 1 organizations linked and 0 failed." in caplog.text
    with caplog.at_level("INFO"):
        await create_client_accounts_for_existing_organizations.main(test_settings)

    await db_session.refresh(organization)
    assert organization.client_account_id == linked_to
    assert await db_session.scalar(select(func.count()).select_from(ClientAccount)) == 1
    assert "0 Client accounts created, 0 organizations linked and 0 failed." in caplog.text


async def test_main_dry_run_reports_without_writing(
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """With `dry_run` the command reports what it would create and link, but persists
    neither the client account nor the link."""
    organization = await organization_factory(operations_external_id="AGR-0007")
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/AGR-0007",
        status_code=200,
        json={
            "id": "AGR-0007",
            "name": "Good Deals Inc",
            "client": {
                "id": "ACC-1000-0007",
                "name": "Client 07",
                "icon": "/v1/accounts/accounts/ACC-0001-0001/icon",
            },
        },
    )
    with caplog.at_level("INFO"):
        await create_client_accounts_for_existing_organizations.main(test_settings, dry_run=True)

    await db_session.refresh(organization)
    assert organization.client_account_id is None
    assert await db_session.scalar(select(func.count()).select_from(ClientAccount)) == 0
    assert (
        "Dry run: 1 client accounts would be created, 1 organizations would be linked and "
        "0 failed." in caplog.text
    )


#
async def test_main_continues_when_an_agreement_cannot_be_retrieved(
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A failed agreement lookup is logged with the organization and counted as failed;
    the remaining organizations are still linked."""
    failing = await organization_factory(operations_external_id="AGR-0008")
    succeeding = await organization_factory(operations_external_id="AGR-0009")
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/AGR-0008",
        status_code=404,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/AGR-0009",
        status_code=200,
        json={
            "id": "AGR-0009",
            "name": "Good Deals Inc",
            "client": {
                "id": "ACC-1000-0009",
                "name": "Client 09",
                "icon": "/v1/accounts/accounts/ACC-0001-0001/icon",
            },
        },
    )
    with caplog.at_level("INFO"):
        await create_client_accounts_for_existing_organizations.main(test_settings)

    await db_session.refresh(failing)
    await db_session.refresh(succeeding)
    assert failing.client_account_id is None
    assert succeeding.client_account_id is not None
    assert f"{failing.id}: Failed to get agreement for AGR-0008" in caplog.text
    assert "1 Client accounts created, 1 organizations linked and 1 failed." in caplog.text


async def test_main_creates_client_account_without_icon(
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    httpx_mock: HTTPXMock,
) -> None:
    """A client without an icon in the agreement yields a client account with a null icon."""
    organization = await organization_factory(operations_external_id="AGR-0010")
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/AGR-0010",
        status_code=200,
        json={
            "id": "AGR-0010",
            "name": "Good Deals Inc",
            "client": {"id": "ACC-1000-0010", "name": "Client 10"},
        },
    )
    await create_client_accounts_for_existing_organizations.main(test_settings)

    await db_session.refresh(organization)
    assert organization.client_account is not None
    assert organization.client_account.icon is None


@pytest.mark.parametrize(
    ("args", "expected_dry_run"),
    [
        pytest.param([], False, id="default"),
        pytest.param(["--dry-run"], True, id="dry-run"),
    ],
)
def test_command_runs_main_with_settings_and_dry_run_flag(
    mocker: MockerFixture,
    test_settings: Settings,
    args: list[str],
    expected_dry_run: bool,
) -> None:
    """The CLI command runs `main` with the settings and the `--dry-run` flag."""
    mock_main_coro = mocker.MagicMock()
    mock_main = mocker.MagicMock(return_value=mock_main_coro)
    mocker.patch("app.commands.create_client_accounts_for_existing_organizations.main", mock_main)
    mock_run = mocker.patch(
        "app.commands.create_client_accounts_for_existing_organizations.asyncio.run"
    )

    result = CliRunner().invoke(app, ["create-client-accounts-for-existing-organizations", *args])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_main_coro)
    mock_main.assert_called_once_with(test_settings, expected_dry_run)
