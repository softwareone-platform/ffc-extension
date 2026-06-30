import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner

from app.cli import app
from app.commands.set_entitlements_tag import set_entitlements_tag
from app.conf import Settings
from app.db.models import Entitlement
from app.enums import EntitlementStatus, TagType
from tests.types import ModelFactory


async def test_set_entitlements_tag(
    test_settings: Settings,
    db_session: AsyncSession,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
):
    ent_tagged = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        linked_datasource_id="ds-tagged",
    )
    ent_untagged = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        linked_datasource_id="ds-untagged",
    )
    await entitlement_factory(
        status=EntitlementStatus.NEW,
        linked_datasource_id="ds-new",
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags?limit=100&and(eq(name,entitlement),in(value,({ent_tagged.id},{ent_untagged.id})))",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={
            "items": [{"name": "entitlement", "value": ent_tagged.id}],
            "limit": 100,
            "offset": 0,
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=201,
        json={
            "resource_id": "ds-untagged",
            "resource_type": TagType.DATA_SOURCE,
            "name": "entitlement",
            "value": ent_untagged.id,
        },
    )

    with caplog.at_level("INFO"):
        await set_entitlements_tag(test_settings)

    assert "Created 1/1 tags" in caplog.text


async def test_set_entitlements_tag_error_getting_tags(
    test_settings: Settings,
    db_session: AsyncSession,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
):
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        linked_datasource_id="ds-1",
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags?limit=100&and(eq(name,entitlement),in(value,({ent.id})))",
        status_code=500,
    )

    with caplog.at_level("INFO"):
        await set_entitlements_tag(test_settings)

    assert "Error getting tags" in caplog.text
    assert "Created 0/0 tags" in caplog.text


async def test_set_entitlements_tag_error_creating_tag(
    test_settings: Settings,
    db_session: AsyncSession,
    entitlement_factory: ModelFactory[Entitlement],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
):
    ent = await entitlement_factory(
        status=EntitlementStatus.ACTIVE,
        linked_datasource_id="ds-1",
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags?limit=100&and(eq(name,entitlement),in(value,({ent.id})))",
        json={"items": [], "limit": 100, "offset": 0},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags",
        status_code=500,
    )

    with caplog.at_level("INFO"):
        await set_entitlements_tag(test_settings)

    assert f"Error creating tag for {ent.id}" in caplog.text
    assert "Created 0/1 tags" in caplog.text


def test_set_entitlements_tag_command(
    mocker: MockerFixture,
    test_settings: Settings,
):
    mock_coro = mocker.MagicMock()
    mock_set_tag = mocker.MagicMock(return_value=mock_coro)

    mocker.patch("app.commands.set_entitlements_tag.set_entitlements_tag", mock_set_tag)
    mock_run = mocker.patch("app.commands.set_entitlements_tag.asyncio.run")
    runner = CliRunner()

    result = runner.invoke(app, ["set-entitlements-tag"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_coro)
    mock_set_tag.assert_called_once_with(test_settings)
