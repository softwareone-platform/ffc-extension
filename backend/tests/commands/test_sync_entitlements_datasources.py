from datetime import UTC, datetime
from typing import Any

import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner

from app.cli import app
from app.commands.sync_entitlements_datasources import sync_entitlements_datasources
from app.conf import Settings
from app.db.models import Entitlement, Organization
from app.enums import DatasourceType, EntitlementStatus, OrganizationStatus, TagType
from tests.types import ModelFactory

LINKED_ORG_ID = "optscale-org-id"
ACCOUNT_ID = "123456789012"


def mock_datasources(
    httpx_mock: HTTPXMock,
    settings: Settings,
    datasources: list[dict[str, Any]],
    linked_organization_id: str = LINKED_ORG_ID,
) -> None:
    """Register the Optscale response listing the organization's datasources."""
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{settings.optscale_rest_api_base_url}/organizations/"
            f"{linked_organization_id}/cloud_accounts?details=false"
        ),
        json={"cloud_accounts": datasources},
    )


def mock_tags(
    httpx_mock: HTTPXMock,
    settings: Settings,
    entitlement_id: str,
    tags: list[dict[str, Any]],
    offset: int = 0,
) -> None:
    """Register the FFC API response listing the entitlement tags."""
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{settings.optscale_ffc_api_base_url}/admin/tags?limit=100&offset={offset}"
            f"&and(eq(name,entitlement),in(value,({entitlement_id})))"
        ),
        json={"items": tags, "limit": 100, "offset": offset},
    )


def datasource(id: str, account_id: str = ACCOUNT_ID, type: str = "aws_cnr") -> dict[str, Any]:
    """Build an Optscale datasource payload."""
    return {"id": id, "account_id": account_id, "type": type, "name": f"Datasource {id}"}


def tag(id: str, resource_id: str, entitlement_id: str) -> dict[str, Any]:
    """Build an FFC API entitlement tag payload."""
    return {
        "id": id,
        "resource_id": resource_id,
        "resource_type": TagType.DATA_SOURCE,
        "name": "entitlement",
        "value": entitlement_id,
    }


def patch_notifications(mocker: MockerFixture) -> tuple[Any, Any]:
    """Patch the Teams notification senders used by the command."""
    module = "app.commands.sync_entitlements_datasources"
    return mocker.patch(f"{module}.send_info"), mocker.patch(f"{module}.send_warning")


def notified_rows(send_mock: Any) -> list[tuple[str, ...]]:
    """Return the table rows of the single notification sent through `send_mock`."""
    send_mock.assert_awaited_once()
    return send_mock.await_args.kwargs["details"].rows


@pytest.fixture
async def linked_organization(organization_factory: ModelFactory[Organization]) -> Organization:
    """An organization linked to an Optscale organization."""
    return await organization_factory(linked_organization_id=LINKED_ORG_ID)


async def test_sync_creates_missing_tag(
    test_settings: Settings,
    linked_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
) -> None:
    """A tag is created for an active entitlement whose datasource has no entitlement tag."""
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-1",
        redeemed_by=linked_organization,
    )
    mock_datasources(httpx_mock, test_settings, [datasource("ds-1")])
    mock_tags(httpx_mock, test_settings, ent.id, [])
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags",
        match_json={
            "resource_id": "ds-1",
            "resource_type": TagType.DATA_SOURCE,
            "name": "entitlement",
            "value": ent.id,
        },
        status_code=201,
    )

    send_info, send_warning = patch_notifications(mocker)
    results = await sync_entitlements_datasources(test_settings)

    assert results.tags_created == 1
    assert results.relinked == 0
    assert results.tags_deleted == 0
    send_info.assert_not_awaited()
    send_warning.assert_not_awaited()


async def test_sync_does_nothing_when_in_sync(
    test_settings: Settings,
    linked_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
) -> None:
    """No change is made when the entitlement datasource and tag are already consistent."""
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-1",
        redeemed_by=linked_organization,
    )
    await entitlement_factory(
        status=EntitlementStatus.TERMINATED,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-1",
        redeemed_by=linked_organization,
    )
    mock_datasources(
        httpx_mock,
        test_settings,
        [datasource("tenant", account_id="tenant", type="azure_tenant"), datasource("ds-1")],
    )
    mock_tags(httpx_mock, test_settings, ent.id, [tag("tag-1", "ds-1", ent.id)])

    results = await sync_entitlements_datasources(test_settings)

    assert results.tags_created == 0
    assert results.relinked == 0
    assert results.tags_deleted == 0
    assert results.failed == 0


async def test_sync_relinks_recreated_datasource(
    test_settings: Settings,
    db_session: AsyncSession,
    linked_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
) -> None:
    """A recreated datasource is relinked, its orphan tag deleted and a new tag created."""
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-old",
        linked_datasource_type=DatasourceType.AWS_CNR,
        redeemed_by=linked_organization,
    )
    mock_datasources(
        httpx_mock, test_settings, [datasource("ds-new", type=DatasourceType.AZURE_CNR)]
    )
    mock_tags(httpx_mock, test_settings, ent.id, [tag("tag-old", "ds-old", ent.id)])
    httpx_mock.add_response(
        method="DELETE",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags/tag-old",
        status_code=204,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags",
        match_json={
            "resource_id": "ds-new",
            "resource_type": TagType.DATA_SOURCE,
            "name": "entitlement",
            "value": ent.id,
        },
        status_code=201,
    )

    send_info, send_warning = patch_notifications(mocker)
    results = await sync_entitlements_datasources(test_settings)

    await db_session.refresh(ent)
    assert ent.linked_datasource_id == "ds-new"
    assert ent.linked_datasource_type == DatasourceType.AZURE_CNR
    assert ent.linked_datasource_name == "Datasource ds-new"
    assert results.relinked == 1
    assert results.tags_deleted == 1
    assert results.tags_created == 1
    send_warning.assert_not_awaited()
    assert send_info.await_args.args == (
        "Sync Entitlements Datasources",
        "1 entitlement has been relinked to a recreated Optscale datasource, 0 errors occurred.",
    )
    assert send_info.await_args.kwargs["details"].header[-1].text == "Old → New ID / Error"
    assert notified_rows(send_info) == [
        (
            f"{ent.id}\t/\t{ent.name}",
            f"{ent.owner.id}\t/\t{ent.owner.name}",
            f"{linked_organization.id}\t/\t{linked_organization.name}",
            f"{ACCOUNT_ID}\t/\tDatasource ds-new",
            "`ds-old` → `ds-new`",
        )
    ]


async def test_sync_keeps_existing_tag_on_recreated_datasource(
    test_settings: Settings,
    linked_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
) -> None:
    """Only the orphan tag is deleted when the recreated datasource is already tagged."""
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-old",
        redeemed_by=linked_organization,
    )
    mock_datasources(httpx_mock, test_settings, [datasource("ds-new")])
    mock_tags(
        httpx_mock,
        test_settings,
        ent.id,
        [tag("tag-old", "ds-old", ent.id), tag("tag-new", "ds-new", ent.id)],
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags/tag-old",
        status_code=204,
    )

    send_info, send_warning = patch_notifications(mocker)
    results = await sync_entitlements_datasources(test_settings)

    assert results.relinked == 1
    assert results.tags_deleted == 1
    assert results.tags_created == 0
    assert notified_rows(send_info)[0][-1] == "`ds-old` → `ds-new`"


async def test_sync_dry_run_persists_nothing(
    test_settings: Settings,
    db_session: AsyncSession,
    linked_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
) -> None:
    """In dry-run mode changes are reported but neither the DB nor the tags are modified."""
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-old",
        redeemed_by=linked_organization,
    )
    mock_datasources(httpx_mock, test_settings, [datasource("ds-new")])
    mock_tags(httpx_mock, test_settings, ent.id, [tag("tag-old", "ds-old", ent.id)])

    send_info, send_warning = patch_notifications(mocker)
    results = await sync_entitlements_datasources(test_settings, dry_run=True)

    await db_session.refresh(ent)
    assert ent.linked_datasource_id == "ds-old"
    assert results.relinked == 1
    assert results.tags_deleted == 1
    assert results.tags_created == 1
    send_info.assert_not_awaited()
    send_warning.assert_not_awaited()


async def test_sync_reports_missing_datasource(
    test_settings: Settings,
    linked_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
) -> None:
    """An entitlement whose datasource no longer exists in Optscale is reported and left as is."""
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-1",
        redeemed_by=linked_organization,
    )
    mock_datasources(httpx_mock, test_settings, [])
    mock_tags(httpx_mock, test_settings, ent.id, [tag("tag-1", "ds-1", ent.id)])

    send_info, send_warning = patch_notifications(mocker)
    with caplog.at_level("WARNING"):
        results = await sync_entitlements_datasources(test_settings)

    assert results.datasources_not_found == 1
    assert f"{ent.id}: datasource {ACCOUNT_ID} not found" in caplog.text
    send_info.assert_not_awaited()
    assert send_warning.await_args.args[1] == (
        "0 entitlements have been relinked to a recreated Optscale datasource, 1 error occurred."
    )
    assert notified_rows(send_warning)[0][-1] == "Datasource not found in Optscale"


async def test_sync_filters_by_organization(
    test_settings: Settings,
    linked_organization: Organization,
    organization_factory: ModelFactory[Organization],
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
) -> None:
    """Only the entitlements redeemed by the given organization are synced."""
    other_organization = await organization_factory(
        operations_external_id="AGR-0000-0000-0000", linked_organization_id="other-org"
    )
    await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        linked_datasource_id="ds-other",
        redeemed_by=other_organization,
    )
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-1",
        redeemed_by=linked_organization,
    )
    mock_datasources(httpx_mock, test_settings, [datasource("ds-1")])
    mock_tags(httpx_mock, test_settings, ent.id, [tag("tag-1", "ds-1", ent.id)])

    results = await sync_entitlements_datasources(
        test_settings, organization_id=linked_organization.id
    )

    assert results.failed == 0


async def test_sync_without_active_entitlements(
    test_settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The command logs and exits when there are no active entitlements to sync."""
    with caplog.at_level("INFO"):
        await sync_entitlements_datasources(test_settings, organization_id="FORG-0000-0000-0000")

    assert "No active entitlements found for organization FORG-0000-0000-0000." in caplog.text
    assert "entitlements relinked" not in caplog.text


async def test_sync_skips_organization_not_linked_to_optscale(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    entitlement_factory: ModelFactory[Entitlement],
    mocker: MockerFixture,
) -> None:
    """Entitlements of an organization without an Optscale link are counted as failed."""
    organization = await organization_factory(linked_organization_id=None)
    await entitlement_factory(status=EntitlementStatus.ACTIVE, redeemed_by=organization)

    send_info, send_warning = patch_notifications(mocker)
    results = await sync_entitlements_datasources(test_settings)

    assert results.failed == 1
    assert notified_rows(send_warning)[0][-1] == "Organization not linked to Optscale"


async def test_sync_fails_organization_when_datasources_cannot_be_fetched(
    test_settings: Settings,
    linked_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
) -> None:
    """Entitlements are counted as failed when Optscale datasources cannot be fetched."""
    await entitlement_factory(status=EntitlementStatus.ACTIVE, redeemed_by=linked_organization)
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.optscale_rest_api_base_url}/organizations/"
            f"{LINKED_ORG_ID}/cloud_accounts?details=false"
        ),
        status_code=500,
        is_reusable=True,
    )

    send_info, send_warning = patch_notifications(mocker)
    results = await sync_entitlements_datasources(test_settings)

    assert results.failed == 1
    details = notified_rows(send_warning)[0][-1]
    assert details.startswith("Error fetching datasources or tags: HTTPStatusError: ")


async def test_sync_fails_entitlement_when_tag_deletion_fails(
    test_settings: Settings,
    linked_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
) -> None:
    """An entitlement is counted as failed when its orphan tag cannot be deleted."""
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-old",
        redeemed_by=linked_organization,
    )
    mock_datasources(httpx_mock, test_settings, [datasource("ds-new")])
    mock_tags(httpx_mock, test_settings, ent.id, [tag("tag-old", "ds-old", ent.id)])
    httpx_mock.add_response(
        method="DELETE",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags/tag-old",
        status_code=500,
        is_reusable=True,
    )

    send_info, send_warning = patch_notifications(mocker)
    results = await sync_entitlements_datasources(test_settings)

    assert results.failed == 1
    assert results.tags_created == 0
    details = notified_rows(send_warning)[0][-1]
    assert details.startswith(
        "Relinked `ds-old` → `ds-new`, but: Error syncing tags: HTTPStatusError: "
    )


async def test_sync_notifies_tag_creation_error_without_relink(
    test_settings: Settings,
    linked_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
) -> None:
    """A tag error on an entitlement that was not relinked is notified without relink details."""
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-1",
        redeemed_by=linked_organization,
    )
    mock_datasources(httpx_mock, test_settings, [datasource("ds-1")])
    mock_tags(httpx_mock, test_settings, ent.id, [])
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags",
        status_code=500,
        is_reusable=True,
    )
    send_info, send_warning = patch_notifications(mocker)

    results = await sync_entitlements_datasources(test_settings)

    assert results.failed == 1
    send_info.assert_not_awaited()
    assert notified_rows(send_warning)[0][-1].startswith("Error syncing tags: HTTPStatusError: ")


async def test_sync_paginates_tags(
    test_settings: Settings,
    linked_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
) -> None:
    """Tags are fetched page by page until a page shorter than the limit is returned."""
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-1",
        redeemed_by=linked_organization,
    )
    mock_datasources(httpx_mock, test_settings, [datasource("ds-1")])
    mock_tags(
        httpx_mock,
        test_settings,
        ent.id,
        [tag(f"tag-{i}", "ds-1", ent.id) for i in range(100)],
    )
    mock_tags(httpx_mock, test_settings, ent.id, [], offset=100)

    results = await sync_entitlements_datasources(test_settings)

    assert results.tags_created == 0
    assert results.failed == 0


@pytest.mark.parametrize(
    ("args", "organization_id", "dry_run"),
    [
        ([], None, False),
        (["--organization", "FORG-1234-5678-9012", "--dry-run"], "FORG-1234-5678-9012", True),
        (["-o", "FORG-1234-5678-9012"], "FORG-1234-5678-9012", False),
    ],
)
def test_sync_entitlements_datasources_command(
    mocker: MockerFixture,
    test_settings: Settings,
    args: list[str],
    organization_id: str | None,
    dry_run: bool,
) -> None:
    """The CLI command forwards the organization filter and dry-run flag to the coroutine."""
    mock_coro = mocker.MagicMock()
    mock_sync = mocker.MagicMock(return_value=mock_coro)
    mocker.patch(
        "app.commands.sync_entitlements_datasources.sync_entitlements_datasources", mock_sync
    )
    mock_run = mocker.patch("app.commands.sync_entitlements_datasources.asyncio.run")

    result = CliRunner().invoke(app, ["sync-entitlements-datasources", *args])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_coro)
    mock_sync.assert_called_once_with(test_settings, organization_id, dry_run)


async def test_sync_warns_about_active_entitlements_of_terminated_organizations(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    entitlement_factory: ModelFactory[Entitlement],
    mocker: MockerFixture,
) -> None:
    """Active entitlements of a terminated organization are not synced but are notified."""
    organization = await organization_factory(
        linked_organization_id=LINKED_ORG_ID, status=OrganizationStatus.TERMINATED
    )
    await entitlement_factory(status=EntitlementStatus.ACTIVE, redeemed_by=organization)
    send_info, send_warning = patch_notifications(mocker)

    results = await sync_entitlements_datasources(test_settings)

    assert results.terminated_organization_entitlements == 1
    send_info.assert_not_awaited()
    assert notified_rows(send_warning)[0][-1] == "Active entitlement for a terminated organization"


async def test_sync_excludes_organizations_with_deleted_status(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    entitlement_factory: ModelFactory[Entitlement],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Active entitlements of organizations in `deleted` status are ignored."""
    organization = await organization_factory(
        linked_organization_id=LINKED_ORG_ID, status=OrganizationStatus.DELETED
    )
    await entitlement_factory(status=EntitlementStatus.ACTIVE, redeemed_by=organization)

    with caplog.at_level("INFO"):
        await sync_entitlements_datasources(test_settings)

    assert "No active entitlements found." in caplog.text


async def test_sync_excludes_soft_deleted_organizations(
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    entitlement_factory: ModelFactory[Entitlement],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Active entitlements of organizations with `deleted_at` set are ignored."""
    organization = await organization_factory(linked_organization_id=LINKED_ORG_ID)
    await entitlement_factory(status=EntitlementStatus.ACTIVE, redeemed_by=organization)
    organization.deleted_at = datetime.now(UTC)
    await db_session.commit()

    with caplog.at_level("INFO"):
        await sync_entitlements_datasources(test_settings)

    assert "No active entitlements found." in caplog.text


async def test_sync_dry_run_logs_entitlements_with_missing_datasource(
    test_settings: Settings,
    linked_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """In dry-run mode entitlements whose datasource is missing are listed in the logs only."""
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-1",
        redeemed_by=linked_organization,
    )
    mock_datasources(httpx_mock, test_settings, [])
    mock_tags(httpx_mock, test_settings, ent.id, [])
    send_info, send_warning = patch_notifications(mocker)

    with caplog.at_level("INFO"):
        await sync_entitlements_datasources(test_settings, dry_run=True)

    send_info.assert_not_awaited()
    send_warning.assert_not_awaited()
    assert (
        f"Dry run: Error: {ent.id} / {ent.name} | {ent.owner.id} / {ent.owner.name} | "
        f"{linked_organization.id} / {linked_organization.name} | {ACCOUNT_ID} / None | "
        "Datasource not found in Optscale"
    ) in caplog.text


async def test_sync_dry_run_logs_relinked_entitlements(
    test_settings: Settings,
    linked_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """In dry-run mode relinked entitlements are listed in the logs with old and new ids."""
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        datasource_id=ACCOUNT_ID,
        linked_datasource_id="ds-old",
        redeemed_by=linked_organization,
    )
    mock_datasources(httpx_mock, test_settings, [datasource("ds-new")])
    mock_tags(httpx_mock, test_settings, ent.id, [tag("tag-new", "ds-new", ent.id)])

    with caplog.at_level("INFO"):
        await sync_entitlements_datasources(test_settings, dry_run=True)

    assert f"Dry run: Relinked: {ent.id} / {ent.name}" in caplog.text
    assert "| `ds-old` → `ds-new`" in caplog.text
