import io
import secrets
from datetime import UTC, datetime, timedelta

import httpx
import jwt
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from app.api_clients.mpt import (
    MPTClient,
    MPTInstallationAuth,
    TokenInfo,
    get_installation_client,
)


def _token(expires: datetime) -> str:
    """Build a JWT whose `exp` claim is the given expiry (helper for token tests)."""
    return jwt.encode({"exp": int(expires.timestamp())}, secrets.token_hex(16), algorithm="HS256")


def _last_request(httpx_mock: HTTPXMock) -> httpx.Request:
    """Return the most recently captured request, asserting one was made."""
    request = httpx_mock.get_request()
    assert request is not None
    return request


def test_token_info_not_expired_for_future_expiry() -> None:
    """`TokenInfo.is_expired` is False when the token expiry is in the future."""
    info = TokenInfo(_token(datetime.now(UTC) + timedelta(hours=1)))
    assert info.is_expired() is False


def test_token_info_expired_for_past_expiry() -> None:
    """`TokenInfo.is_expired` is True when the token expiry is in the past."""
    info = TokenInfo(_token(datetime.now(UTC) - timedelta(hours=1)))
    assert info.is_expired() is True


async def test_installation_auth_fetches_token_then_authorizes_request(
    httpx_mock: HTTPXMock,
) -> None:
    """`MPTInstallationAuth` requests a token, then sends the request with a Bearer header."""
    token = _token(datetime.now(UTC) + timedelta(hours=1))
    httpx_mock.add_response(method="POST", json={"token": token})
    httpx_mock.add_response(method="GET", json={"id": "ACC-1"})

    client = MPTClient(MPTInstallationAuth("ACC-1"))
    result = await client.get_account("ACC-1")

    assert result == {"id": "ACC-1"}
    requests = httpx_mock.get_requests()
    assert requests[0].url.path.endswith("/integration/installations/-/token")
    assert requests[1].headers["Authorization"] == f"Bearer {token}"


async def test_installation_auth_reuses_unexpired_token(httpx_mock: HTTPXMock) -> None:
    """`MPTInstallationAuth` does not refresh a still-valid token on subsequent requests."""
    token = _token(datetime.now(UTC) + timedelta(hours=1))
    httpx_mock.add_response(method="POST", json={"token": token})
    httpx_mock.add_response(method="GET", json={"id": "ACC-1"})
    httpx_mock.add_response(method="GET", json={"id": "ACC-2"})

    client = MPTClient(MPTInstallationAuth("ACC-1"))
    await client.get_account("ACC-1")
    await client.get_account("ACC-2")

    token_posts = [r for r in httpx_mock.get_requests() if r.method == "POST"]
    assert len(token_posts) == 1


async def test_get_appends_select_query(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.get` appends the `select` fields as a query parameter to the resource URL."""
    httpx_mock.add_response(method="GET", json={"id": "USR-1"})
    result = await mpt_extension_client.get("accounts/users", "USR-1", select=["name", "email"])
    assert result == {"id": "USR-1"}
    assert _last_request(httpx_mock).url.query.decode() == "select=name,email"


async def test_get_collection_builds_query_and_select(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.get_collection` joins the query and select clauses into the request URL."""
    httpx_mock.add_response(method="GET", json={"data": []})
    await mpt_extension_client.get_collection(
        "accounts/users", query="eq(status,Active)", select=["name"]
    )
    query = _last_request(httpx_mock).url.query.decode()
    assert "eq(status,Active)" in query
    assert "select=name" in query


async def test_get_collection_without_clauses(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.get_collection` requests the bare endpoint when no clauses are given."""
    httpx_mock.add_response(method="GET", json={"data": []})
    await mpt_extension_client.get_collection("accounts/users")
    assert _last_request(httpx_mock).url.query == b""


async def test_create_posts_payload(mpt_extension_client: MPTClient, httpx_mock: HTTPXMock) -> None:
    """`MPTClient.create` POSTs the payload and returns the parsed response body."""
    httpx_mock.add_response(method="POST", json={"id": "OBJ-1"})
    result = await mpt_extension_client.create("billing/journals", {"name": "j"})
    assert result == {"id": "OBJ-1"}


async def test_update_puts_payload(mpt_extension_client: MPTClient, httpx_mock: HTTPXMock) -> None:
    """`MPTClient.update` PUTs the payload to the resource URL and returns the response body."""
    httpx_mock.add_response(method="PUT", json={"id": "TSK-1", "status": "done"})
    result = await mpt_extension_client.update_task("TSK-1", {"status": "done"})
    assert result == {"id": "TSK-1", "status": "done"}


async def test_delete_issues_delete_request(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.delete` issues a DELETE request and returns None."""
    httpx_mock.add_response(method="DELETE", status_code=204)
    await mpt_extension_client.delete_journal_attachment("JOU-1", "ATT-1")
    assert _last_request(httpx_mock).method == "DELETE"


async def test_run_object_action_posts_to_action_url(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.run_object_action` POSTs to the `<id>/<action>` URL and returns the body."""
    httpx_mock.add_response(method="POST", json={"id": "TSK-1"})
    result = await mpt_extension_client.start_task("TSK-1")
    assert result == {"id": "TSK-1"}
    assert _last_request(httpx_mock).url.path.endswith("system/tasks/TSK-1/execute")


async def test_complete_task_posts_payload(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.complete_task` POSTs to the task `complete` action."""
    httpx_mock.add_response(method="POST", json={"id": "TSK-1"})
    await mpt_extension_client.complete_task("TSK-1", {"result": "ok"})
    assert _last_request(httpx_mock).url.path.endswith("system/tasks/TSK-1/complete")


async def test_get_page_includes_pagination_and_select(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.get_page` includes limit, offset, query, and select in the request URL."""
    httpx_mock.add_response(method="GET", json={"data": [], "$meta": {"pagination": {"total": 0}}})
    await mpt_extension_client.get_page(
        "commerce/orders", limit=5, offset=10, query="eq(a,1)", select=["id"]
    )
    query = _last_request(httpx_mock).url.query.decode()
    assert "limit=5" in query
    assert "offset=10" in query
    assert "eq(a,1)" in query
    assert "select=id" in query


async def test_get_first_returns_first_item(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.get_first` returns the first item of the page when present."""
    httpx_mock.add_response(
        method="GET",
        json={"data": [{"id": "A"}, {"id": "B"}], "$meta": {"pagination": {"total": 2}}},
    )
    assert await mpt_extension_client.get_first("commerce/orders") == {"id": "A"}


async def test_get_first_returns_none_for_empty_page(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.get_first` returns None when the page contains no items."""
    httpx_mock.add_response(method="GET", json={"data": [], "$meta": {"pagination": {"total": 0}}})
    assert await mpt_extension_client.get_first("commerce/orders") is None


async def test_count_returns_pagination_total(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.count` returns the pagination total reported by the page meta."""
    httpx_mock.add_response(method="GET", json={"data": [], "$meta": {"pagination": {"total": 42}}})
    assert await mpt_extension_client.count("commerce/orders") == 42


async def test_collection_iterator_paginates_across_pages(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, mocker: MockerFixture
) -> None:
    """`MPTClient.collection_iterator` walks every page until the total is exhausted."""
    mocker.patch.object(mpt_extension_client.settings, "mpt_api_rows_per_page", 1)
    httpx_mock.add_response(
        method="GET", json={"data": [{"id": "A"}], "$meta": {"pagination": {"total": 2}}}
    )
    httpx_mock.add_response(
        method="GET", json={"data": [{"id": "B"}], "$meta": {"pagination": {"total": 2}}}
    )
    items = [item async for item in mpt_extension_client.get_orders()]
    assert items == [{"id": "A"}, {"id": "B"}]


async def test_get_user_targets_users_endpoint(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.get_user` reads from the accounts/users endpoint."""
    httpx_mock.add_response(method="GET", json={"id": "USR-1"})
    await mpt_extension_client.get_user("USR-1")
    assert _last_request(httpx_mock).url.path.endswith("accounts/users/USR-1")


async def test_get_token_targets_api_tokens_endpoint(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.get_token` reads from the accounts/api-tokens endpoint."""
    httpx_mock.add_response(method="GET", json={"id": "TKN-1"})
    await mpt_extension_client.get_token("TKN-1")
    assert _last_request(httpx_mock).url.path.endswith("accounts/api-tokens/TKN-1")


async def test_get_task_targets_tasks_endpoint(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.get_task` reads from the system/tasks endpoint."""
    httpx_mock.add_response(method="GET", json={"id": "TSK-1"})
    await mpt_extension_client.get_task("TSK-1")
    assert _last_request(httpx_mock).url.path.endswith("system/tasks/TSK-1")


async def test_get_order_targets_orders_endpoint(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.get_order` reads from the commerce/orders endpoint."""
    httpx_mock.add_response(method="GET", json={"id": "ORD-1"})
    await mpt_extension_client.get_order("ORD-1")
    assert _last_request(httpx_mock).url.path.endswith("commerce/orders/ORD-1")


async def test_upload_journal_charges_posts_file(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock
) -> None:
    """`MPTClient.upload_journal_charges` uploads the charges file to the journal upload URL."""
    httpx_mock.add_response(method="POST", status_code=200)
    charges = io.BytesIO(b"{}")
    charges.name = "charges.jsonl"
    await mpt_extension_client.upload_journal_charges("JOU-1", charges)
    assert _last_request(httpx_mock).url.path.endswith("billing/journals/JOU-1/upload")


def test_get_installation_client_is_cached_per_account() -> None:
    """`get_installation_client` returns the same cached client instance for an account id."""
    first = get_installation_client("ACC-CACHE-1")
    second = get_installation_client("ACC-CACHE-1")
    assert first is second
