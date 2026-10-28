import json
import logging
import secrets
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import jwt
import pytest
from httpx import Response
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from app.api_clients.mpt import get_installation_client
from app.conf import Settings
from app.schemas.core import Event, ExtensionContext
from tests.types import EventFactory

EXTENSION_ACCOUNT_ID = "ACC-0000-0000"
AFFILIATE_ACCOUNT_ID = "ACC-3333-3333"
OTHER_ACCOUNT_ID = "ACC-9999-9999"


def _installation_token() -> str:
    """A JWT the installation auth flow accepts (only `exp` is read)."""
    expires = datetime.now(UTC) + timedelta(hours=1)
    return jwt.encode({"exp": int(expires.timestamp())}, secrets.token_hex(16), algorithm="HS256")


def _mock_installation_token(httpx_mock: HTTPXMock, base_url: str, account_id: str) -> None:
    """The installation client exchanges the extension token for an account token first."""
    # `get_installation_client` is cached per account for the whole process, so a token
    # fetched by an earlier test would be reused here and this response never requested.
    get_installation_client.cache_clear()
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/integration/installations/-/token",
        match_params={"account.id": account_id},
        json={"token": _installation_token()},
    )


def _mocker_order_task_claim(
    httpx_mock: HTTPXMock,
    base_url: str,
    task_id: str,
    ext_ctx: ExtensionContext,
    owner_account_id: str = EXTENSION_ACCOUNT_ID,
):
    parameters = {"accountId": owner_account_id}

    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/system/tasks/{task_id}",
        json={"id": task_id, "parameters": parameters},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/system/tasks/{task_id}/execute",
        json={"id": task_id, "parameters": parameters},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{base_url}/system/tasks/{task_id}",
        match_json={"parameters": {**parameters, "instanceId": ext_ctx.instance_id.upper()}},
        json={"id": task_id},
    )


def _mock_subscription_task_claim(
    httpx_mock: HTTPXMock, base_url: str, task_id: str, ext_ctx: ExtensionContext
):
    parameters = {"accountId": EXTENSION_ACCOUNT_ID}
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/system/tasks/{task_id}/execute",
        json={"id": task_id, "parameters": parameters},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{base_url}/system/tasks/{task_id}",
        match_json={"parameters": {**parameters, "instanceId": ext_ctx.instance_id.upper()}},
        json={"id": task_id},
    )


def _task_log_body(httpx_mock: HTTPXMock, base_url: str, task_id: str) -> dict[str, Any]:
    """The JSON body of the single task log entry the lifecycle wrote."""
    request = httpx_mock.get_request(method="POST", url=f"{base_url}/system/tasks/{task_id}/logs")
    assert request is not None
    return json.loads(request.content)


def _teams_card(httpx_mock: HTTPXMock, webhook_url: str) -> dict[str, Any]:
    """The adaptive card posted to Teams: `{"title": ..., "text": ..., "raw": ...}`."""
    request = httpx_mock.get_request(method="POST", url=webhook_url)
    assert request is not None
    envelope = json.loads(request.content)
    body = envelope["attachments"][0]["content"]["body"]
    return {"title": body[0]["text"], "text": body[1]["text"], "raw": request.content.decode()}


# -- apply_result fails: the error propagates and Teams is notified --


async def test_process_order_propagates_a_failed_task_log(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
) -> None:
    """A rejected task log entry is posted to Teams and re-raised; the task is not completed."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    base_url = test_settings.mpt_api_base_url
    event = event_factory(object_id=purchase_order["id"])
    # A task owned by another account resolves to COMPLETE without touching the order.

    _mocker_order_task_claim(
        httpx_mock, base_url, event.task.id, mocked_extension_ctx, owner_account_id=OTHER_ACCOUNT_ID
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/system/tasks/{event.task.id}/logs",
        status_code=httpx.codes.INTERNAL_SERVER_ERROR,
    )
    httpx_mock.add_response(
        method="POST", url=test_settings.msteams_notifications_webhook_url, status_code=202
    )

    with pytest.raises(httpx.HTTPStatusError, match="500"):
        await post_order_event(event)

    # The claim ran to the ownership guard; writing its Info outcome is what failed.
    task_url = f"{base_url}/system/tasks/{event.task.id}"
    assert len(httpx_mock.get_requests(method="GET", url=task_url)) == 1
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/execute")) == 1
    assert len(httpx_mock.get_requests(method="PUT", url=task_url)) == 1
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/logs")) == 1
    log_body = _task_log_body(httpx_mock, base_url, event.task.id)
    assert log_body["task"] == {"id": event.task.id}
    assert log_body["severity"] == "Info"
    assert "not the fulfillment owner" in log_body["message"]
    assert OTHER_ACCOUNT_ID in log_body["message"]

    # Nothing moved the task and the order was never looked at.
    assert not httpx_mock.get_requests(url=f"{task_url}/complete")
    assert not httpx_mock.get_requests(url=f"{task_url}/fail")
    assert not httpx_mock.get_requests(url=f"{task_url}/reschedule")
    assert not [
        request
        for request in httpx_mock.get_requests()
        if "/integration/installations/" in request.url.path
        or "/commerce/orders/" in request.url.path
    ]

    # The rejected log write is posted to Teams once, with the traceback and the event details.
    webhook_url = test_settings.msteams_notifications_webhook_url
    assert webhook_url is not None
    assert len(httpx_mock.get_requests(url=webhook_url)) == 1
    card = _teams_card(httpx_mock, webhook_url)
    assert "Process Event Error" in card["title"]
    assert "HTTPStatusError" in card["text"]
    assert "500" in card["text"]
    assert "log_task" in card["text"]
    assert event.id in card["raw"]
    assert event.task.id in card["raw"]
    assert purchase_order["id"] in card["raw"]
    assert mocked_extension_ctx.instance_id in card["raw"]


async def test_process_order_still_propagates_the_original_error_when_teams_is_down(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A failing Teams send is logged and swallowed; the original failure is what propagates."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    base_url = test_settings.mpt_api_base_url
    event = event_factory(object_id=purchase_order["id"])
    _mocker_order_task_claim(
        httpx_mock, base_url, event.task.id, mocked_extension_ctx, owner_account_id=OTHER_ACCOUNT_ID
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/system/tasks/{event.task.id}/logs",
        status_code=httpx.codes.INTERNAL_SERVER_ERROR,
    )
    httpx_mock.add_exception(
        httpx.ConnectError("teams unreachable"),
        method="POST",
        url=test_settings.msteams_notifications_webhook_url,
    )

    with pytest.raises(httpx.HTTPStatusError, match="500"):
        await post_order_event(event)

    # The claim ran to the ownership guard; writing its Info outcome is what failed.
    task_url = f"{base_url}/system/tasks/{event.task.id}"
    assert len(httpx_mock.get_requests(method="GET", url=task_url)) == 1
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/execute")) == 1
    assert len(httpx_mock.get_requests(method="PUT", url=task_url)) == 1
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/logs")) == 1
    log_body = _task_log_body(httpx_mock, base_url, event.task.id)
    assert log_body["task"] == {"id": event.task.id}
    assert log_body["severity"] == "Info"
    assert OTHER_ACCOUNT_ID in log_body["message"]

    # Nothing moved the task and the order was never looked at.
    assert not httpx_mock.get_requests(url=f"{task_url}/complete")
    assert not httpx_mock.get_requests(url=f"{task_url}/fail")
    assert not httpx_mock.get_requests(url=f"{task_url}/reschedule")
    assert not [
        request
        for request in httpx_mock.get_requests()
        if "/integration/installations/" in request.url.path
        or "/commerce/orders/" in request.url.path
    ]

    # Teams was tried exactly once; the connect error is logged with its traceback and swallowed.
    assert len(httpx_mock.get_requests(url=test_settings.msteams_notifications_webhook_url)) == 1
    notification_failures = [
        record
        for record in caplog.records
        if "notification" in record.getMessage() and record.exc_info is not None
    ]
    assert len(notification_failures) == 1
    assert notification_failures[0].levelno == logging.ERROR
    assert event.task.id in notification_failures[0].getMessage()
    notification_exc_info = notification_failures[0].exc_info
    assert notification_exc_info is not None
    assert isinstance(notification_exc_info[1], httpx.ConnectError)

    # The original failure was logged too, before the notification was attempted.
    unexpected_failures = [
        record
        for record in caplog.records
        if "failed unexpectedly" in record.getMessage() and record.exc_info is not None
    ]
    assert len(unexpected_failures) == 1
    assert event.task.id in unexpected_failures[0].getMessage()
    assert purchase_order["id"] in unexpected_failures[0].getMessage()
    unexpected_exc_info = unexpected_failures[0].exc_info
    assert unexpected_exc_info is not None
    assert isinstance(unexpected_exc_info[1], httpx.HTTPStatusError)
    assert caplog.records.index(unexpected_failures[0]) < caplog.records.index(
        notification_failures[0]
    )


async def test_process_order_propagates_a_failed_task_completion(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
) -> None:
    """A failed `complete_task` after a successful log entry is posted to Teams and re-raised."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    base_url = test_settings.mpt_api_base_url
    event = event_factory(object_id=purchase_order["id"])
    _mocker_order_task_claim(
        httpx_mock, base_url, event.task.id, mocked_extension_ctx, owner_account_id=OTHER_ACCOUNT_ID
    )
    httpx_mock.add_response(
        method="POST", url=f"{base_url}/system/tasks/{event.task.id}/logs", json={"id": "LOG-1"}
    )
    # POSTs are not retried by the transport, so one timeout is terminal.
    httpx_mock.add_exception(
        httpx.ReadTimeout("timed out"),
        method="POST",
        url=f"{base_url}/system/tasks/{event.task.id}/complete",
    )
    httpx_mock.add_response(
        method="POST", url=test_settings.msteams_notifications_webhook_url, status_code=202
    )

    with pytest.raises(httpx.ReadTimeout, match="timed out"):
        await post_order_event(event)

    # The claim ran to the ownership guard and its Info outcome was logged before completing.
    task_url = f"{base_url}/system/tasks/{event.task.id}"
    assert len(httpx_mock.get_requests(method="GET", url=task_url)) == 1
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/execute")) == 1
    assert len(httpx_mock.get_requests(method="PUT", url=task_url)) == 1
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/logs")) == 1
    log_body = _task_log_body(httpx_mock, base_url, event.task.id)
    assert log_body["task"] == {"id": event.task.id}
    assert log_body["severity"] == "Info"
    assert "not the fulfillment owner" in log_body["message"]
    assert OTHER_ACCOUNT_ID in log_body["message"]

    # The completion was attempted exactly once and nothing else moved the task.
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/complete")) == 1
    assert not httpx_mock.get_requests(url=f"{task_url}/fail")
    assert not httpx_mock.get_requests(url=f"{task_url}/reschedule")

    # The order was never looked at.
    assert not [
        request
        for request in httpx_mock.get_requests()
        if "/integration/installations/" in request.url.path
        or "/commerce/orders/" in request.url.path
    ]

    # The timeout is posted to Teams once, with the traceback and the event details.
    webhook_url = test_settings.msteams_notifications_webhook_url
    assert webhook_url is not None
    assert len(httpx_mock.get_requests(url=webhook_url)) == 1
    card = _teams_card(httpx_mock, webhook_url)
    assert "Process Event Error" in card["title"]
    assert "httpx.ReadTimeout: timed out" in card["text"]
    assert "complete_task" in card["text"]
    assert event.id in card["raw"]
    assert event.task.id in card["raw"]
    assert purchase_order["id"] in card["raw"]
    assert mocked_extension_ctx.instance_id in card["raw"]


# -- unexpected errors before the outcome is decided --


async def test_process_order_reports_an_unreadable_order_as_unexpected(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
) -> None:
    """A non-JSON order payload is not a known error: Teams is notified and it propagates."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    base_url = test_settings.mpt_api_base_url
    event = event_factory(object_id=purchase_order["id"])
    _mocker_order_task_claim(httpx_mock, base_url, event.task.id, mocked_extension_ctx)
    _mock_installation_token(httpx_mock, base_url, EXTENSION_ACCOUNT_ID)
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        text="<html>some text</html>",
    )
    httpx_mock.add_response(
        method="POST", url=test_settings.msteams_notifications_webhook_url, status_code=202
    )

    with pytest.raises(ValueError, match="Expecting value"):
        await post_order_event(event)

    # The failure is posted to Teams once, with the traceback and the event details.
    webhook_url = test_settings.msteams_notifications_webhook_url
    assert webhook_url is not None
    assert len(httpx_mock.get_requests(url=webhook_url)) == 1
    card = _teams_card(httpx_mock, webhook_url)
    assert "Process Event Error" in card["title"]
    assert "JSONDecodeError" in card["text"]
    assert event.id in card["raw"]
    assert event.task.id in card["raw"]
    assert purchase_order["id"] in card["raw"]
    assert mocked_extension_ctx.instance_id in card["raw"]

    # The task was claimed, then left in Processing: no log entry and no transition.
    task_url = f"{base_url}/system/tasks/{event.task.id}"
    assert len(httpx_mock.get_requests(method="GET", url=task_url)) == 1
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/execute")) == 1
    assert len(httpx_mock.get_requests(method="PUT", url=task_url)) == 1
    assert not httpx_mock.get_requests(url=f"{task_url}/logs")
    assert not httpx_mock.get_requests(url=f"{task_url}/complete")
    assert not httpx_mock.get_requests(url=f"{task_url}/fail")
    assert not httpx_mock.get_requests(url=f"{task_url}/reschedule")

    # The order was read once and never written.
    order_url = f"{base_url}/commerce/orders/{purchase_order['id']}"
    assert (
        len(
            httpx_mock.get_requests(
                method="POST",
                url=f"{base_url}/integration/installations/-/token",
                match_params={"account.id": EXTENSION_ACCOUNT_ID},
            )
        )
        == 1
    )
    assert (
        len(
            httpx_mock.get_requests(
                method="GET", url=order_url, match_params={"select": "subscriptions.lines"}
            )
        )
        == 1
    )
    assert not [
        request
        for request in httpx_mock.get_requests()
        if "/commerce/orders/" in request.url.path and request.method != "GET"
    ]


async def test_process_order_reports_a_malformed_task_as_unexpected(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
) -> None:
    """A task without `parameters.accountId` is unexpected: notified, re-raised, never executed."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    base_url = test_settings.mpt_api_base_url
    event = event_factory(object_id=purchase_order["id"])
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/system/tasks/{event.task.id}",
        json={"id": event.task.id, "parameters": {}},
    )
    httpx_mock.add_response(
        method="POST", url=test_settings.msteams_notifications_webhook_url, status_code=202
    )

    with pytest.raises(KeyError, match="accountId"):
        await post_order_event(event)

    # The failure is posted to Teams once, with the traceback and the event details.
    webhook_url = test_settings.msteams_notifications_webhook_url
    assert webhook_url is not None
    assert len(httpx_mock.get_requests(url=webhook_url)) == 1
    card = _teams_card(httpx_mock, webhook_url)
    assert "Process Event Error" in card["title"]
    assert "KeyError: 'accountId'" in card["text"]
    assert event.id in card["raw"]
    assert event.task.id in card["raw"]
    assert purchase_order["id"] in card["raw"]
    assert mocked_extension_ctx.instance_id in card["raw"]

    # The task was only read: nothing was started, logged or transitioned.
    task_url = f"{base_url}/system/tasks/{event.task.id}"
    assert len(httpx_mock.get_requests(method="GET", url=task_url)) == 1
    assert not httpx_mock.get_requests(url=f"{task_url}/execute")
    assert not httpx_mock.get_requests(method="PUT", url=task_url)
    assert not httpx_mock.get_requests(url=f"{task_url}/logs")
    assert not httpx_mock.get_requests(url=f"{task_url}/complete")
    assert not httpx_mock.get_requests(url=f"{task_url}/fail")
    assert not httpx_mock.get_requests(url=f"{task_url}/reschedule")

    # The order is never looked at.
    assert not httpx_mock.get_requests(url=f"{base_url}/integration/installations/-/token")
    assert not [
        request for request in httpx_mock.get_requests() if "/commerce/orders/" in request.url.path
    ]


# -- known errors: applied to the task, never posted to Teams --


async def test_process_order_reschedules_when_claiming_the_task_fails(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
) -> None:
    """A marketplace error while starting the task is known: logged on the task, rescheduled."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    base_url = test_settings.mpt_api_base_url
    event = event_factory(object_id=purchase_order["id"])
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/system/tasks/{event.task.id}",
        json={"id": event.task.id, "parameters": {"accountId": EXTENSION_ACCOUNT_ID}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/system/tasks/{event.task.id}/execute",
        status_code=httpx.codes.INTERNAL_SERVER_ERROR,
    )
    httpx_mock.add_response(
        method="POST", url=f"{base_url}/system/tasks/{event.task.id}/logs", json={"id": "LOG-1"}
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/system/tasks/{event.task.id}/reschedule",
        json={"id": event.task.id},
    )

    response = await post_order_event(event)

    assert response.status_code == 200
    assert response.json() == {"response": "Delay", "delay": test_settings.reschedule_seconds}

    # The claim stopped at the failing start call: no instance id written, no other transition.
    task_url = f"{base_url}/system/tasks/{event.task.id}"
    assert len(httpx_mock.get_requests(method="GET", url=task_url)) == 1
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/execute")) == 1
    assert not httpx_mock.get_requests(method="PUT", url=task_url)
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/reschedule")) == 1
    assert not httpx_mock.get_requests(url=f"{task_url}/complete")
    assert not httpx_mock.get_requests(url=f"{task_url}/fail")

    # One Error log entry naming the failed call, the order and the upstream response.
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/logs")) == 1
    log_body = _task_log_body(httpx_mock, base_url, event.task.id)
    assert log_body["task"] == {"id": event.task.id}
    assert log_body["severity"] == "Error"
    assert log_body["message"] == (
        f"claim_task failed for {purchase_order['id']} "
        f"POST {httpx.URL(task_url).path}/execute 500 Internal Server Error"
    )

    # The order is never looked at: no installation token, no order read or write, no Teams card.
    assert not [
        request
        for request in httpx_mock.get_requests()
        if "/integration/installations/" in request.url.path
        or "/commerce/orders/" in request.url.path
    ]
    assert not httpx_mock.get_requests(url=test_settings.msteams_notifications_webhook_url)


async def test_process_order_does_not_notify_for_a_task_owned_by_another_account(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
) -> None:
    """A task owned by another account is a routine known outcome: closed, no Teams card."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    base_url = test_settings.mpt_api_base_url
    event = event_factory(object_id=purchase_order["id"])
    _mocker_order_task_claim(
        httpx_mock, base_url, event.task.id, mocked_extension_ctx, owner_account_id=OTHER_ACCOUNT_ID
    )
    httpx_mock.add_response(
        method="POST", url=f"{base_url}/system/tasks/{event.task.id}/logs", json={"id": "LOG-1"}
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/system/tasks/{event.task.id}/complete",
        json={"id": event.task.id},
    )

    response = await post_order_event(event)

    assert response.status_code == 200
    assert response.json() == {"response": "OK", "delay": None}

    # The task is started before ownership is checked, then closed; nothing else moves it.
    task_url = f"{base_url}/system/tasks/{event.task.id}"
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/execute")) == 1
    assert len(httpx_mock.get_requests(method="PUT", url=task_url)) == 1
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/complete")) == 1
    assert not httpx_mock.get_requests(url=f"{task_url}/fail")
    assert not httpx_mock.get_requests(url=f"{task_url}/reschedule")

    # One Info log entry explaining why the task was ignored.
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/logs")) == 1
    log_body = _task_log_body(httpx_mock, base_url, event.task.id)
    assert log_body["task"] == {"id": event.task.id}
    assert log_body["severity"] == "Info"
    assert "not the fulfillment owner" in log_body["message"]
    assert OTHER_ACCOUNT_ID in log_body["message"]
    assert mocked_extension_ctx.account_id in log_body["message"]
    assert purchase_order["id"] in log_body["message"]

    # The ownership guard short-circuits before the order is ever looked at.
    assert not [
        request
        for request in httpx_mock.get_requests()
        if "/integration/installations/" in request.url.path
        or "/commerce/orders/" in request.url.path
    ]
    assert not httpx_mock.get_requests(url=test_settings.msteams_notifications_webhook_url)


async def test_process_order_does_not_notify_for_an_unsupported_order_type(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
) -> None:
    """An unsupported order type is a known domain error: cancelled on the task, no Teams card."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    base_url = test_settings.mpt_api_base_url
    event = event_factory(object_id=purchase_order["id"])
    _mocker_order_task_claim(httpx_mock, base_url, event.task.id, mocked_extension_ctx)
    _mock_installation_token(httpx_mock, base_url, EXTENSION_ACCOUNT_ID)
    httpx_mock.add_response(
        method="GET",
        url=f"{base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json={**purchase_order, "type": "Configuration"},
    )
    httpx_mock.add_response(
        method="POST", url=f"{base_url}/system/tasks/{event.task.id}/logs", json={"id": "LOG-1"}
    )

    response = await post_order_event(event)

    assert response.status_code == 200
    assert response.json() == {"response": "Cancel", "delay": None}

    # The task was claimed before the order type was inspected.
    task_url = f"{base_url}/system/tasks/{event.task.id}"
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/execute")) == 1
    assert len(httpx_mock.get_requests(method="PUT", url=task_url)) == 1

    # The known error is written to the task log once, as a warning naming the type.
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/logs")) == 1
    log_body = _task_log_body(httpx_mock, base_url, event.task.id)
    assert log_body["task"] == {"id": event.task.id}
    assert log_body["severity"] == "Warning"
    assert log_body["message"] == "Configuration"

    # Cancel leaves the task where it is, never touches the order, and posts nothing to Teams.
    assert not httpx_mock.get_requests(url=f"{task_url}/complete")
    assert not httpx_mock.get_requests(url=f"{task_url}/fail")
    assert not httpx_mock.get_requests(url=f"{task_url}/reschedule")
    assert not [
        request
        for request in httpx_mock.get_requests()
        if "/commerce/orders/" in request.url.path and request.method != "GET"
    ]
    assert not httpx_mock.get_requests(url=test_settings.msteams_notifications_webhook_url)


# -- subscriptions share the lifecycle --


async def test_process_subscription_propagates_a_failed_task_log(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_subscription_event: Callable[[Event], Awaitable[Response]],
) -> None:
    """The subscription route follows the same rule: a rejected log entry is notified and raised."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    base_url = test_settings.mpt_api_base_url
    subscription_id = "SUB-0000-0000"
    event = event_factory(
        object_id=subscription_id, object_name="subscription", object_type="Subscription"
    )
    _mock_subscription_task_claim(httpx_mock, base_url, event.task.id, mocked_extension_ctx)
    _mock_installation_token(httpx_mock, base_url, AFFILIATE_ACCOUNT_ID)
    httpx_mock.add_response(
        method="GET", url=f"{base_url}/commerce/subscriptions/{subscription_id}", json={}
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{base_url}/system/tasks/{event.task.id}/logs",
        status_code=httpx.codes.SERVICE_UNAVAILABLE,
    )
    httpx_mock.add_response(
        method="POST", url=test_settings.msteams_notifications_webhook_url, status_code=202
    )

    with pytest.raises(httpx.HTTPStatusError, match="503"):
        await post_subscription_event(event)

    # The lifecycle got as far as applying the "not found" outcome before the log call failed.
    task_url = f"{base_url}/system/tasks/{event.task.id}"
    assert len(httpx_mock.get_requests(method="POST", url=f"{task_url}/logs")) == 1
    log_body = _task_log_body(httpx_mock, base_url, event.task.id)
    assert log_body["task"] == {"id": event.task.id}
    assert log_body["severity"] == "Error"
    assert log_body["message"] == f"No subscription found for {subscription_id}."

    # The failure is posted to Teams once, with the traceback and the event details.
    webhook_url = test_settings.msteams_notifications_webhook_url
    assert webhook_url is not None
    assert len(httpx_mock.get_requests(url=webhook_url)) == 1
    card = _teams_card(httpx_mock, webhook_url)
    assert "Process Event Error" in card["title"]
    assert "HTTPStatusError" in card["text"]
    assert "503" in card["text"]
    assert event.id in card["raw"]
    assert event.task.id in card["raw"]
    assert subscription_id in card["raw"]
    assert "Subscription" in card["raw"]
    assert mocked_extension_ctx.instance_id in card["raw"]

    # The task is left in Processing for the platform to redeliver.
    assert not httpx_mock.get_requests(url=f"{task_url}/complete")
    assert not httpx_mock.get_requests(url=f"{task_url}/fail")
    assert not httpx_mock.get_requests(url=f"{task_url}/reschedule")
