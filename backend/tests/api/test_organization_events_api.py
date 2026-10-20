import uuid
from collections.abc import Callable
from typing import Any

import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from app.conf import Settings
from app.db.models import Organization
from app.enums import EventLevel
from tests.types import ModelFactory


async def test_get_events_for_organization_returns_upstream_events(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    ffc_api_event_payload_factory: Callable[..., dict[str, Any]],
    httpx_mock: HTTPXMock,
    admin_client: AsyncClient,
) -> None:
    """The events endpoint returns the FFC API events of the linked organization as a page."""
    org = await organization_factory(linked_organization_id=str(uuid.uuid4()))
    event = ffc_api_event_payload_factory(
        ack=True,
        acknowledged="2026-10-02T08:30:00Z",
        acknowledged_by="USR-1",
        acknowledged_user="Peter Parker",
        resolution="Bucket permissions fixed",
        initiator_id="USR-2",
        initiator_name="Mary Jane",
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/events?limit=50&offset=0",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={"items": [event], "total": 1, "limit": 50, "offset": 0},
    )

    response = await admin_client.get(f"/organizations/{org.id}/events")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                **event,
                "time": "2026-10-01T10:00:00Z",
                "acknowledged": "2026-10-02T08:30:00Z",
            }
        ],
        "total": 1,
        "limit": 50,
        "offset": 0,
    }


async def test_get_events_for_organization_forwards_rql_and_pagination(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    httpx_mock: HTTPXMock,
    admin_client: AsyncClient,
) -> None:
    """The events endpoint forwards the RQL expression and pagination to the FFC API as-is."""
    org = await organization_factory(linked_organization_id=str(uuid.uuid4()))
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/events"
            "?limit=10&offset=20&in(level,(ERROR,WARNING))=&gte(time,2026-10-01T00:00:00Z)="
            "&order_by(-time)="
        ),
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={"items": [], "total": 25, "limit": 10, "offset": 20},
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/events"
        "?in(level,(ERROR,WARNING))&gte(time,2026-10-01T00:00:00Z)&order_by(-time)"
        "&limit=10&offset=20"
    )

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 25, "limit": 10, "offset": 20}


@pytest.mark.parametrize(
    ("upstream_level", "expected_level"),
    [
        pytest.param("INFO", EventLevel.INFO, id="info"),
        pytest.param("WARNING", EventLevel.WARNING, id="warning"),
        pytest.param("ERROR", EventLevel.ERROR, id="error"),
        pytest.param("DEBUG", EventLevel.UNKNOWN, id="unknown"),
    ],
)
async def test_get_events_for_organization_maps_level(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    ffc_api_event_payload_factory: Callable[..., dict[str, Any]],
    httpx_mock: HTTPXMock,
    admin_client: AsyncClient,
    upstream_level: str,
    expected_level: EventLevel,
) -> None:
    """The events endpoint maps the upstream level to `EventLevel`, falling back to `UNKNOWN`."""
    org = await organization_factory(linked_organization_id=str(uuid.uuid4()))
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/events?limit=50&offset=0",
        json={
            "items": [ffc_api_event_payload_factory(level=upstream_level)],
            "total": 1,
            "limit": 50,
            "offset": 0,
        },
    )

    response = await admin_client.get(f"/organizations/{org.id}/events")

    assert response.status_code == 200
    assert response.json()["items"][0]["level"] == expected_level.value


async def test_get_events_for_organization_ignores_unknown_upstream_fields(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    ffc_api_event_payload_factory: Callable[..., dict[str, Any]],
    httpx_mock: HTTPXMock,
    admin_client: AsyncClient,
) -> None:
    """The events endpoint drops fields the FFC API adds that aren't part of the schema."""
    org = await organization_factory(linked_organization_id=str(uuid.uuid4()))
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/events?limit=50&offset=0",
        json={
            "items": [ffc_api_event_payload_factory(localized="N0022")],
            "total": 1,
            "limit": 50,
            "offset": 0,
        },
    )

    response = await admin_client.get(f"/organizations/{org.id}/events")

    assert response.status_code == 200
    assert "localized" not in response.json()["items"][0]


async def test_get_events_for_missing_organization(admin_client: AsyncClient) -> None:
    """The events endpoint returns 404 when the organization doesn't exist."""
    org_id = "FORG-1234-5678-9012"

    response = await admin_client.get(f"/organizations/{org_id}/events")

    assert response.status_code == 404
    assert response.json() == {"detail": f"Organization with ID `{org_id}` wasn't found."}


async def test_get_events_for_organization_with_no_linked_organization_id(
    organization_factory: ModelFactory[Organization],
    admin_client: AsyncClient,
) -> None:
    """The events endpoint returns 400 when the organization has no linked FFC organization."""
    org = await organization_factory(linked_organization_id=None)

    response = await admin_client.get(f"/organizations/{org.id}/events")

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"Organization {org.name} has no associated FinOps for Cloud organization."
    }


@pytest.mark.parametrize("upstream_status_code", [400, 500])
async def test_get_events_for_organization_with_ffc_api_error(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    httpx_mock: HTTPXMock,
    admin_client: AsyncClient,
    upstream_status_code: int,
) -> None:
    """The events endpoint reports any FFC API error as a 502 carrying the upstream status."""
    org = await organization_factory(linked_organization_id=str(uuid.uuid4()))
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/events?limit=50&offset=0",
        status_code=upstream_status_code,
        text="Unsupported filter",
    )

    response = await admin_client.get(f"/organizations/{org.id}/events")

    assert response.status_code == 502
    assert response.json() == {
        "detail": (
            f"Error fetching events for organization {org.name}: "
            f"{upstream_status_code} - Unsupported filter."
        )
    }


async def test_get_events_for_organization_forbidden_for_affiliate(
    organization_factory: ModelFactory[Organization],
    affiliate_client: AsyncClient,
) -> None:
    """The events endpoint returns 403 for affiliate accounts."""
    org = await organization_factory(linked_organization_id=str(uuid.uuid4()))

    response = await affiliate_client.get(f"/organizations/{org.id}/events")

    assert response.status_code == 403
