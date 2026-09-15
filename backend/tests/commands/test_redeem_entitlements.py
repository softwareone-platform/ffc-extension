from datetime import UTC, datetime

import pytest
import time_machine
from httpx import HTTPStatusError, ReadTimeout
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner

from app.cli import app
from app.commands.redeem_entitlements import fetch_datasources_for_organization, redeem_entitlements
from app.conf import Settings
from app.db.models import Entitlement, Organization
from app.enums import DatasourceType, EntitlementStatus
from app.notifications import ColumnHeader
from tests.types import ModelFactory


@time_machine.travel("2025-03-07T10:00:00Z", tick=False)
async def test_redeeem_entitlements(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    apple_inc_organization: Organization,
    entitlement_aws: Entitlement,
    entitlement_gcp: Entitlement,
    entitlement_gcp_with_redeem_at: Entitlement,
    httpx_mock: HTTPXMock,
):
    mocker.patch(
        "app.commands.redeem_entitlements.fetch_datasources_for_organization",
        return_value=[
            {
                "id": "aws",
                "name": "AWS Datasource",
                "type": "aws_cnr",
                "account_id": entitlement_aws.datasource_id,
            },
            {
                "id": "ds2",
                "name": "azure ds",
                "type": "azure_cnr",
                "account_id": entitlement_gcp_with_redeem_at.datasource_id,
            },
            {"id": "ds3", "name": "gcp ds", "type": "gcp_cnr", "account_id": "gcp-account-id"},
            {
                "id": "ds4",
                "name": "aws tenant ds",
                "type": "aws_tenant",
                "account_id": "aws-tentant-id",
            },
            {
                "id": "ds5",
                "name": "azure tenant ds",
                "type": "azure_tenant",
                "account_id": "azure-tentant-id",
            },
            {
                "id": "ds",
                "name": "gcp tenant ds",
                "type": "gcp_tenant",
                "account_id": "gcp-tentant-id",
            },
            {
                "id": "gcp",
                "name": "GCP Datasource",
                "type": "gcp_cnr",
                "account_id": entitlement_gcp.datasource_id,
            },
        ],
    )
    mocked_send_info = mocker.patch(
        "app.commands.redeem_entitlements.send_info",
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=201,
        is_reusable=True,
    )

    await redeem_entitlements(test_settings)

    await db_session.refresh(entitlement_aws)
    assert entitlement_aws.linked_datasource_id == "aws"
    assert entitlement_aws.linked_datasource_name == "AWS Datasource"
    assert entitlement_aws.linked_datasource_type == DatasourceType.AWS_CNR
    assert entitlement_aws.status == EntitlementStatus.ACTIVE
    assert entitlement_aws.redeemed_by == apple_inc_organization
    assert entitlement_aws.redeemed_at is not None
    assert entitlement_aws.redeemed_at == datetime.now(UTC)

    await db_session.refresh(entitlement_gcp)
    assert entitlement_gcp.linked_datasource_id == "gcp"
    assert entitlement_gcp.linked_datasource_name == "GCP Datasource"
    assert entitlement_gcp.linked_datasource_type == DatasourceType.GCP_CNR
    assert entitlement_gcp.status == EntitlementStatus.ACTIVE
    assert entitlement_gcp.redeemed_by == apple_inc_organization
    assert entitlement_gcp.redeemed_at is not None
    assert entitlement_gcp.redeemed_at == datetime.now(UTC)

    await db_session.refresh(entitlement_gcp_with_redeem_at)
    assert entitlement_gcp_with_redeem_at.linked_datasource_id == "ds2"
    assert entitlement_gcp_with_redeem_at.linked_datasource_name == "azure ds"
    assert entitlement_gcp_with_redeem_at.linked_datasource_type == DatasourceType.AZURE_CNR
    assert entitlement_gcp_with_redeem_at.status == EntitlementStatus.ACTIVE
    assert entitlement_gcp_with_redeem_at.redeemed_by == apple_inc_organization
    assert entitlement_gcp_with_redeem_at.redeemed_at == entitlement_gcp_with_redeem_at.redeem_at

    assert mocked_send_info.await_count == 1
    assert mocked_send_info.await_args is not None
    assert mocked_send_info.await_args.args == (
        "Redeem Entitlements Success",
        "3 Entitlements have been successfully redeemed.",
    )
    assert mocked_send_info.await_args.kwargs["details"].header == (
        ColumnHeader("Entitlement", width="stretch"),
        ColumnHeader("Owner", width="stretch"),
        ColumnHeader("Organization", width="stretch"),
        ColumnHeader("Datasource", width="stretch"),
    )
    assert len(mocked_send_info.await_args.kwargs["details"].rows) == 3


async def test_redeeem_entitlements_error_fetching_datasources(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    test_settings: Settings,
    apple_inc_organization: Organization,
    entitlement_aws: Entitlement,
    db_session: AsyncSession,
):
    mocker.patch(
        "app.commands.redeem_entitlements.fetch_datasources_for_organization",
        side_effect=ReadTimeout("timed out"),
    )
    mocker_send_exception = mocker.patch(
        "app.commands.redeem_entitlements.send_exception",
    )
    with caplog.at_level("ERROR"):
        await redeem_entitlements(test_settings)

    assert "Failed to fetch datasources" in caplog.text
    assert "timed out" in caplog.text
    await db_session.refresh(entitlement_aws)
    assert entitlement_aws.status == EntitlementStatus.NEW
    assert entitlement_aws.redeemed_by is None
    mocker_send_exception.assert_awaited_once_with(
        "Redeem Entitlements Error",
        (
            f"Failed to fetch datasources for organization "
            f"{apple_inc_organization.id} (ReadTimeout): timed out"
        ),
    )


async def test_redeeem_entitlements_error_creating_tag(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    apple_inc_organization: Organization,
    entitlement_aws: Entitlement,
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
):
    mocker.patch(
        "app.commands.redeem_entitlements.fetch_datasources_for_organization",
        return_value=[
            {
                "id": "aws",
                "name": "AWS Datasource",
                "type": "aws_cnr",
                "account_id": entitlement_aws.datasource_id,
            },
        ],
    )
    mocked_send_info = mocker.patch(
        "app.commands.redeem_entitlements.send_info",
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=500,
    )

    with caplog.at_level("INFO"):
        await redeem_entitlements(test_settings)

    assert "Could not create entitlement tag for datasource" in caplog.text

    assert mocked_send_info.await_args.args == (
        "Redeem Entitlements Success",
        "1 Entitlement has been successfully redeemed.",
    )

    assert mocked_send_info.await_count == 1
    assert len(mocked_send_info.await_args.kwargs["details"].rows) == 1


async def test_redeem_entitlements_skips_datasource_with_an_active_entitlement(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    apple_inc_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
) -> None:
    """A datasource whose entitlement is already active is left untouched."""
    redeemed_at = datetime(2025, 1, 1, tzinfo=UTC)
    active_entitlement = await entitlement_factory(
        name="Already redeemed",
        datasource_id="datasource-account-id",
        linked_datasource_id="ds1",
        linked_datasource_type=DatasourceType.AWS_CNR,
        status=EntitlementStatus.ACTIVE,
        redeemed_at=redeemed_at,
        redeemed_by=apple_inc_organization,
    )
    mocker.patch(
        "app.commands.redeem_entitlements.fetch_datasources_for_organization",
        return_value=[
            {
                "id": "ds1",
                "name": "AWS Datasource",
                "type": "aws_cnr",
                "account_id": "datasource-account-id",
            },
        ],
    )
    mocked_send_info = mocker.patch("app.commands.redeem_entitlements.send_info")
    mocked_send_warning = mocker.patch("app.commands.redeem_entitlements.send_warning")

    await redeem_entitlements(test_settings)

    await db_session.refresh(active_entitlement)
    assert active_entitlement.status == EntitlementStatus.ACTIVE
    assert active_entitlement.redeemed_at == redeemed_at
    mocked_send_info.assert_not_awaited()
    mocked_send_warning.assert_not_awaited()


async def test_redeem_entitlements_reports_duplicates_and_skips_if_one_is_active(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    apple_inc_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
) -> None:
    """Duplicates are reported and nothing is redeemed when one of them is already active."""
    active_entitlement = await entitlement_factory(
        name="Already redeemed",
        datasource_id="datasource-account-id",
        linked_datasource_id="ds1",
        linked_datasource_type=DatasourceType.AWS_CNR,
        status=EntitlementStatus.ACTIVE,
        redeemed_at=datetime(2025, 1, 1, tzinfo=UTC),
        redeemed_by=apple_inc_organization,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    new_entitlement = await entitlement_factory(
        name="Duplicate",
        datasource_id="datasource-account-id",
        created_at=datetime(2025, 2, 1, tzinfo=UTC),
    )
    mocker.patch(
        "app.commands.redeem_entitlements.fetch_datasources_for_organization",
        return_value=[
            {
                "id": "ds1",
                "name": "AWS Datasource",
                "type": "aws_cnr",
                "account_id": "datasource-account-id",
            },
        ],
    )
    mocked_send_info = mocker.patch("app.commands.redeem_entitlements.send_info")
    mocked_send_warning = mocker.patch("app.commands.redeem_entitlements.send_warning")

    await redeem_entitlements(test_settings)

    await db_session.refresh(new_entitlement)
    assert new_entitlement.status == EntitlementStatus.NEW
    assert new_entitlement.redeemed_by is None
    assert new_entitlement.linked_datasource_id is None

    mocked_send_info.assert_not_awaited()
    assert mocked_send_warning.await_count == 1
    assert mocked_send_warning.await_args is not None
    assert mocked_send_warning.await_args.args == (
        "Redeem Entitlements Duplicates",
        (
            "1 datasource has multiple entitlements in `new` or `active` status "
            f"for the organization {apple_inc_organization.id} - {apple_inc_organization.name}."
        ),
    )
    assert mocked_send_warning.await_args.kwargs["details"].header == (
        ColumnHeader("Datasource", width="stretch"),
        ColumnHeader("Entitlement", width="stretch"),
        ColumnHeader("Owner", width="stretch"),
        ColumnHeader("Status", width="auto"),
    )
    rows = mocked_send_warning.await_args.kwargs["details"].rows
    assert len(rows) == 2
    assert [row[1] for row in rows] == [
        f"{active_entitlement.id}\t/\t{active_entitlement.name}",
        f"{new_entitlement.id}\t/\t{new_entitlement.name}",
    ]
    assert [row[3] for row in rows] == ["active", "new"]


@time_machine.travel("2025-03-07T10:00:00Z", tick=False)
async def test_redeem_entitlements_redeems_the_oldest_of_multiple_new_entitlements(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    apple_inc_organization: Organization,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
) -> None:
    """The oldest of several new entitlements is redeemed and the duplicates are reported."""
    oldest_entitlement = await entitlement_factory(
        name="Oldest",
        datasource_id="datasource-account-id",
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    newest_entitlement = await entitlement_factory(
        name="Newest",
        datasource_id="datasource-account-id",
        created_at=datetime(2025, 2, 1, tzinfo=UTC),
    )
    mocker.patch(
        "app.commands.redeem_entitlements.fetch_datasources_for_organization",
        return_value=[
            {
                "id": "ds1",
                "name": "AWS Datasource",
                "type": "aws_cnr",
                "account_id": "datasource-account-id",
            },
        ],
    )
    mocked_send_info = mocker.patch("app.commands.redeem_entitlements.send_info")
    mocked_send_warning = mocker.patch("app.commands.redeem_entitlements.send_warning")
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=201,
    )

    await redeem_entitlements(test_settings)

    await db_session.refresh(oldest_entitlement)
    assert oldest_entitlement.status == EntitlementStatus.ACTIVE
    assert oldest_entitlement.redeemed_by == apple_inc_organization
    assert oldest_entitlement.redeemed_at == datetime.now(UTC)
    assert oldest_entitlement.linked_datasource_id == "ds1"

    await db_session.refresh(newest_entitlement)
    assert newest_entitlement.status == EntitlementStatus.NEW
    assert newest_entitlement.redeemed_by is None
    assert newest_entitlement.linked_datasource_id is None

    assert mocked_send_info.await_count == 1
    assert mocked_send_info.await_args is not None
    assert mocked_send_info.await_args.args == (
        "Redeem Entitlements Success",
        "1 Entitlement has been successfully redeemed.",
    )
    assert len(mocked_send_info.await_args.kwargs["details"].rows) == 1

    assert mocked_send_warning.await_count == 1
    assert mocked_send_warning.await_args is not None
    rows = mocked_send_warning.await_args.kwargs["details"].rows
    assert len(rows) == 2
    assert [row[1] for row in rows] == [
        f"{oldest_entitlement.id}\t/\t{oldest_entitlement.name}",
        f"{newest_entitlement.id}\t/\t{newest_entitlement.name}",
    ]


async def test_fetch_datasources_for_organization(
    test_settings: Settings,
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
):
    datasources = [
        {"id": "ds1", "type": "aws_cnr", "account_id": "aws-account-id"},
    ]
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/organizations/linked_organization_id/cloud_accounts?details=false",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={
            "cloud_accounts": datasources,
        },
    )

    fetched_datasources = await fetch_datasources_for_organization(
        test_settings, "linked_organization_id"
    )
    assert datasources == fetched_datasources


async def test_fetch_datasources_for_organization_error(
    test_settings: Settings,
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
):
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/organizations/linked_organization_id/cloud_accounts?details=false",
        status_code=500,
    )

    with pytest.raises(HTTPStatusError, match="Internal Server Error"):
        await fetch_datasources_for_organization(test_settings, "linked_organization_id")


def test_redeem_entitlements_command(
    mocker: MockerFixture,
    test_settings: Settings,
):
    mock_redeem_coro = mocker.MagicMock()
    mock_redeem_entitlements = mocker.MagicMock(return_value=mock_redeem_coro)

    mocker.patch("app.commands.redeem_entitlements.redeem_entitlements", mock_redeem_entitlements)
    mock_run = mocker.patch("app.commands.redeem_entitlements.asyncio.run")
    runner = CliRunner()

    # Run the command
    result = runner.invoke(
        app,
        ["redeem-entitlements"],
    )
    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_redeem_coro)

    mock_redeem_entitlements.assert_called_once_with(
        test_settings,
    )
