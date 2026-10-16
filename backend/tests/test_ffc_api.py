import httpx
import pytest
from pytest_httpx import HTTPXMock

from app.api_clients.ffc_api import FFCAPIClient, resolve_params
from app.conf import Settings


def test_resolve_params_empty_when_no_arguments() -> None:
    """`resolve_params` returns an empty list when no limit, offset, or rql is given."""
    assert resolve_params() == []


def test_resolve_params_includes_limit_and_offset() -> None:
    """`resolve_params` emits stringified limit and offset tuples when provided."""
    assert resolve_params(limit=10, offset=5) == [("limit", "10"), ("offset", "5")]


def test_resolve_params_keeps_zero_limit_and_offset() -> None:
    """`resolve_params` includes limit/offset of 0 since only `None` is skipped."""
    assert resolve_params(limit=0, offset=0) == [("limit", "0"), ("offset", "0")]


def test_resolve_params_splits_rql_clauses() -> None:
    """`resolve_params` splits an `&`-joined rql string into individual empty-valued clauses."""
    assert resolve_params(rql="eq(a,1)&eq(b,2)") == [("eq(a,1)", ""), ("eq(b,2)", "")]


def test_resolve_params_combines_pagination_and_rql() -> None:
    """`resolve_params` combines pagination params and rql clauses in order."""
    assert resolve_params(limit=1, offset=2, rql="eq(a,1)") == [
        ("limit", "1"),
        ("offset", "2"),
        ("eq(a,1)", ""),
    ]


async def test_create_user_posts_payload_to_admin_users(
    ffc_api_client: FFCAPIClient, test_settings: Settings, httpx_mock: HTTPXMock
) -> None:
    """`create_user` POSTs the user payload to `/admin/users` authenticated by cluster secret."""
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/users",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        match_json={
            "email": "peter.parker@spiderman.com",
            "display_name": "Peter Parker",
            "password": "s3cret",
        },
        json={"id": "USR-1"},
        status_code=201,
    )

    response = await ffc_api_client.create_user(
        email="peter.parker@spiderman.com", display_name="Peter Parker", password="s3cret"
    )

    assert response.json() == {"id": "USR-1"}


async def test_create_organization_posts_payload_to_admin_organizations(
    ffc_api_client: FFCAPIClient, test_settings: Settings, httpx_mock: HTTPXMock
) -> None:
    """`create_organization` POSTs the org payload to `/admin/organizations` with cluster secret."""
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        match_json={"org_name": "ACME", "user_id": "USR-1", "currency": "EUR"},
        json={"id": "ORG-1"},
        status_code=201,
    )

    response = await ffc_api_client.create_organization(
        org_name="ACME", user_id="USR-1", currency="EUR"
    )

    assert response.json() == {"id": "ORG-1"}


@pytest.mark.parametrize(
    ("method_name", "kwargs"),
    [
        pytest.param(
            "create_user",
            {"email": "a@b.c", "display_name": "A B", "password": "x"},
            id="create_user",
        ),
        pytest.param(
            "create_organization",
            {"org_name": "ACME", "user_id": "USR-1", "currency": "EUR"},
            id="create_organization",
        ),
    ],
)
async def test_create_methods_raise_on_error_status(
    ffc_api_client: FFCAPIClient,
    httpx_mock: HTTPXMock,
    method_name: str,
    kwargs: dict[str, str],
) -> None:
    """The create methods raise `httpx.HTTPStatusError` when the FFC API returns an error."""
    httpx_mock.add_response(method="POST", status_code=400)

    with pytest.raises(httpx.HTTPStatusError, match="400 Bad Request"):
        await getattr(ffc_api_client, method_name)(**kwargs)
