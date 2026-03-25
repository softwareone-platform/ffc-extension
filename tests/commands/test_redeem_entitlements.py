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


@time_machine.travel("2025-03-07T10:00:00Z", tick=False)
async def test_redeeem_entitlements(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    apple_inc_organization: Organization,
    entitlement_aws: Entitlement,
    entitlement_gcp: Entitlement,
    entitlement_gcp_with_redeem_at: Entitlement,
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
