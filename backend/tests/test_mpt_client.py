import io
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from app.api_clients.mpt import (
    MPTClient,
    MPTInstallationAuth,
    TokenInfo,
    get_installation_client,
)
from app.conf import Settings


def _token(expires: datetime) -> str:
    """Build a JWT whose `exp` claim is the given expiry (helper for token tests)."""
    return jwt.encode({"exp": int(expires.timestamp())}, secrets.token_hex(16), algorithm="HS256")


def test_token_info_not_expired_for_future_expiry() -> None:
    """`TokenInfo.is_expired` is False when the token expiry is in the future."""
    info = TokenInfo(_token(datetime.now(UTC) + timedelta(hours=1)))
    assert info.is_expired() is False


def test_token_info_expired_for_past_expiry() -> None:
    """`TokenInfo.is_expired` is True when the token expiry is in the past."""
    info = TokenInfo(_token(datetime.now(UTC) - timedelta(hours=1)))
    assert info.is_expired() is True


async def test_installation_auth_fetches_token_then_authorizes_request(
    httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTInstallationAuth` requests a token, then sends the request with a Bearer header."""
    base_url = test_settings.mpt_api_base_url
    token = _token(datetime.now(UTC) + timedelta(hours=1))
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/integration/installations/-/token?account.id=ACC-1",
        json={"token": token},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/accounts/accounts/ACC-1",
        match_headers={"Authorization": f"Bearer {token}"},
        json={"id": "ACC-1"},
    )

    client = MPTClient(MPTInstallationAuth("ACC-1"))
    result = await client.get_account("ACC-1")

    assert result == {"id": "ACC-1"}


async def test_installation_auth_reuses_unexpired_token(
    httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTInstallationAuth` does not refresh a still-valid token on subsequent requests."""
    base_url = test_settings.mpt_api_base_url
    token = _token(datetime.now(UTC) + timedelta(hours=1))
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/integration/installations/-/token?account.id=ACC-1",
        json={"token": token},
    )
    httpx_mock.add_response(
        method="GET", url=f"{base_url}/accounts/accounts/ACC-1", json={"id": "ACC-1"}
    )
    httpx_mock.add_response(
        method="GET", url=f"{base_url}/accounts/accounts/ACC-2", json={"id": "ACC-2"}
    )

    client = MPTClient(MPTInstallationAuth("ACC-1"))
    await client.get_account("ACC-1")
    await client.get_account("ACC-2")

    assert len(httpx_mock.get_requests(method="POST")) == 1


async def test_get_appends_select_query(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.get` appends the `select` fields as a query parameter to the resource URL."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="GET", url=f"{base_url}/accounts/users/USR-1?select=name,email", json={"id": "USR-1"}
    )
    result = await mpt_extension_client.get("accounts/users", "USR-1", select=["name", "email"])
    assert result == {"id": "USR-1"}


async def test_get_collection_builds_query_and_select(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.get_collection` joins the query and select clauses into the request URL."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/accounts/users?eq(status,Active)&select=name",
        json={"data": []},
    )
    await mpt_extension_client.get_collection(
        "accounts/users", query="eq(status,Active)", select=["name"]
    )


async def test_get_collection_without_clauses(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.get_collection` requests the bare endpoint when no clauses are given."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(method="GET", url=f"{base_url}/accounts/users", json={"data": []})
    await mpt_extension_client.get_collection("accounts/users")


async def test_create_posts_payload(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.create` POSTs the payload and returns the parsed response body."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/billing/journals",
        match_json={"name": "j"},
        json={"id": "OBJ-1"},
    )
    result = await mpt_extension_client.create("billing/journals", {"name": "j"})
    assert result == {"id": "OBJ-1"}


async def test_update_puts_payload(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.update` PUTs the payload to the resource URL and returns the response body."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="PUT",
        url=f"{base_url}/system/tasks/TSK-1",
        match_json={"status": "done"},
        json={"id": "TSK-1", "status": "done"},
    )
    result = await mpt_extension_client.update_task("TSK-1", {"status": "done"})
    assert result == {"id": "TSK-1", "status": "done"}


async def test_delete_issues_delete_request(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.delete` issues a DELETE request to the attachment URL and returns None."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="DELETE",
        url=f"{base_url}/billing/journals/JOU-1/attachments/ATT-1",
        status_code=204,
    )
    await mpt_extension_client.delete_journal_attachment("JOU-1", "ATT-1")


async def test_run_object_action_posts_to_action_url(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.run_object_action` POSTs to the `<id>/<action>` URL and returns the body."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/system/tasks/TSK-1/execute",
        json={"id": "TSK-1", "parameters": {}},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{base_url}/system/tasks/TSK-1",
        match_json={"parameters": {"instanceId": "INSTANCE_ID"}},
        json={"id": "TSK-1", "parameters": {"instance_id": "instance_id"}},
    )
    result = await mpt_extension_client.start_task("TSK-1", "instance_id")
    assert result == {"id": "TSK-1", "parameters": {"instance_id": "instance_id"}}


async def test_complete_task_posts_payload(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.complete_task` POSTs to the task `complete` action."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/system/tasks/TSK-1/complete",
        match_json={"result": "ok"},
        json={"id": "TSK-1"},
    )
    await mpt_extension_client.complete_task("TSK-1", {"result": "ok"})


async def test_get_page_includes_pagination_and_select(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.get_page` includes limit, offset, query, and select in the request URL."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/commerce/orders?eq(a,1)&select=id&limit=5&offset=10",
        json={"data": [], "$meta": {"pagination": {"total": 0}}},
    )
    await mpt_extension_client.get_page(
        "commerce/orders", limit=5, offset=10, query="eq(a,1)", select=["id"]
    )


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
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.get_user` reads from the accounts/users endpoint."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="GET", url=f"{base_url}/accounts/users/USR-1", json={"id": "USR-1"}
    )
    await mpt_extension_client.get_user("USR-1")


async def test_get_token_targets_api_tokens_endpoint(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.get_token` reads from the accounts/api-tokens endpoint."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="GET", url=f"{base_url}/accounts/api-tokens/TKN-1", json={"id": "TKN-1"}
    )
    await mpt_extension_client.get_token("TKN-1")


async def test_get_task_targets_tasks_endpoint(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.get_task` reads from the system/tasks endpoint."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="GET", url=f"{base_url}/system/tasks/TSK-1", json={"id": "TSK-1"}
    )
    await mpt_extension_client.get_task("TSK-1")


async def test_get_order_targets_orders_endpoint(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.get_order` reads from the commerce/orders endpoint."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="GET", url=f"{base_url}/commerce/orders/ORD-1", json={"id": "ORD-1"}
    )
    await mpt_extension_client.get_order("ORD-1")


async def test_upload_journal_charges_posts_file(
    mpt_extension_client: MPTClient, httpx_mock: HTTPXMock, test_settings: Settings
) -> None:
    """`MPTClient.upload_journal_charges` uploads the charges file to the journal upload URL."""
    base_url = test_settings.mpt_api_base_url
    httpx_mock.add_response(
        method="POST", url=f"{base_url}/billing/journals/JOU-1/upload", status_code=200
    )
    charges = io.BytesIO(b"{}")
    charges.name = "charges.jsonl"
    await mpt_extension_client.upload_journal_charges("JOU-1", charges)


def test_get_installation_client_is_cached_per_account() -> None:
    """`get_installation_client` returns the same cached client instance for an account id."""
    first = get_installation_client("ACC-CACHE-1")
    second = get_installation_client("ACC-CACHE-1")
    assert first is second
