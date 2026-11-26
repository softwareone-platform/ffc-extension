"""Activity log of order events: purchase and termination orders are recorded as operations."""

import copy
from typing import Any

import pytest
from freezegun import freeze_time
from pytest_httpx import HTTPXMock
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.activity import ActivityOperation
from app.conf import Settings
from app.db.constants import APP_ACTOR_ID
from app.db.models import ActivityLog, Organization
from app.enums import ActivityStatus
from app.events.orders.constants import QUERYING_TEMPLATE_TYPE
from app.events.orders.error import (
    ERR_DUE_DATE_IS_REACHED,
    ERR_DUE_DATE_NOT_SET,
    ERR_ORDER_TYPE_NOT_SUPPORTED,
    ERR_ORGANIZATION_NAME,
)
from app.events.orders.processing import OrderEventHandler
from app.events.processing import ProcessingStatus
from app.parameters import PARAM_ORGANIZATION_NAME, get_ordering_parameter, set_due_date
from tests.types import ActivityLogFetcher, ModelFactory, OrderFactory, OrderMocker

# The change records of a purchase that provisions a new organization.
PROVISIONING_CHANGES = [
    ("client_accounts", "insert"),
    ("organizations", "insert"),
    ("organizations", "update"),
]

# The change records of the termination of an organization with two active entitlements.
TERMINATION_CHANGES = sorted(
    [
        ("organizations", "update"),
        ("entitlements", "update"),
        ("entitlements", "update"),
        ("entitlements", "insert"),
        ("entitlements", "insert"),
        ("termination_feedbacks", "insert"),
    ]
)


def change_kinds(entry: ActivityLog) -> list[tuple[str, str]]:
    """The table of each change record of `entry`, and whether the row was inserted,
    updated or deleted."""
    kinds = []
    for change in entry.changes:
        if change.before is None:
            kind = "insert"
        elif change.after is None:
            kind = "delete"
        else:
            kind = "update"
        kinds.append((change.object_type, kind))
    return kinds


# -- purchase -------------------------------------------------------------------------


async def test_purchase_order_is_one_completed_provisioning_entry_by_the_application(
    purchase_order: dict[str, Any],
    purchase_order_mocker: OrderMocker,
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
    db_session: AsyncSession,
) -> None:
    """A purchase that goes through first time is one completed `organization.provisioned`
    entry by the application, keyed by the order, with the provisioning summary."""
    order_id = purchase_order["id"]
    agreement_id = purchase_order["agreement"]["id"]
    purchase_order_mocker()
    processor = await order_event_handler.get_processor(object_id=order_id)

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    organization = await db_session.scalar(
        select(Organization).where(Organization.operations_external_id == agreement_id)
    )
    assert organization is not None
    [entry] = await fetch_operation_entries(f"order:{order_id}")
    assert entry.action == "organization.provisioned"
    assert entry.status == ActivityStatus.COMPLETED
    assert entry.recorded_by_id == APP_ACTOR_ID
    assert entry.message == (
        f"FinOps for Cloud service provisioned for organization 'ACME Inc' "
        f"({organization.id}), agreement {agreement_id}: admin pl@example.com (new user). "
        f"Purchase order {order_id}."
    )


async def test_purchase_order_entry_records_the_client_account_and_the_linked_organization(
    purchase_order: dict[str, Any],
    purchase_order_mocker: OrderMocker,
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """The entry of a purchase records the client account and the organization inserted,
    then the organization linked to its FinOps for Cloud organization."""
    purchase_order_mocker()
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    await processor.process()

    [entry] = await fetch_operation_entries(f"order:{purchase_order['id']}")
    assert change_kinds(entry) == PROVISIONING_CHANGES
    link = entry.changes[-1]
    assert link.before is not None
    assert link.before["linked_organization_id"] is None
    assert link.after is not None
    assert link.after["linked_organization_id"] == "OPT-ORG-0001"


async def test_purchase_order_entry_notes_each_step_of_a_new_user_purchase(
    purchase_order: dict[str, Any],
    purchase_order_mocker: OrderMocker,
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
    db_session: AsyncSession,
) -> None:
    """The entry of a purchase for a new user notes, by the application, each step: the
    user and the organization created, the agreement linked, the password reset sent, then
    the completion."""
    purchase_order_mocker()
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    await processor.process()

    agreement_id = purchase_order["agreement"]["id"]
    organization_id = await db_session.scalar(
        select(Organization.id).where(Organization.operations_external_id == agreement_id)
    )
    [entry] = await fetch_operation_entries(f"order:{purchase_order['id']}")
    assert [note.message for note in entry.notes] == [
        "FinOps for Cloud user employee-id (pl@example.com) created.",
        "FinOps for Cloud organization OPT-ORG-0001 created.",
        f"Agreement {agreement_id} linked to organization {organization_id} in Marketplace.",
        "Password reset email sent to pl@example.com.",
        "Completed.",
    ]
    assert {note.recorded_by_id for note in entry.notes} == {APP_ACTOR_ID}


async def test_purchase_order_entry_notes_the_existing_user_made_admin(
    purchase_order: dict[str, Any],
    purchase_order_mocker: OrderMocker,
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """The entry of a purchase whose admin already has a FinOps for Cloud user notes that
    user, and no password reset."""
    purchase_order_mocker(new_user=False)
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    await processor.process()

    [entry] = await fetch_operation_entries(f"order:{purchase_order['id']}")
    notes = [note.message for note in entry.notes]
    assert notes[0] == "FinOps for Cloud user employee-id (pl@example.com) already exists."
    assert not any(note.startswith("Password reset") for note in notes)


async def test_purchase_order_failed_password_reset_is_noted_on_the_completed_entry(
    purchase_order: dict[str, Any],
    purchase_order_mocker: OrderMocker,
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """A password reset that fails is noted, and the purchase still completes its entry."""
    purchase_order_mocker(reset_password_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    [entry] = await fetch_operation_entries(f"order:{purchase_order['id']}")
    assert entry.status == ActivityStatus.COMPLETED
    assert [note.message for note in entry.notes][-2:] == [
        "Password reset email to pl@example.com could not be sent.",
        "Completed.",
    ]


@freeze_time("2024-12-01")
async def test_purchase_order_retried_after_a_failed_agreement_update_completes_its_entry(
    purchase_order: dict[str, Any],
    purchase_order_mocker: OrderMocker,
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """A purchase whose agreement update fails is retried on the same entry, which notes
    the failure and is completed by the retry that links the agreement."""
    order_id = purchase_order["id"]
    purchase_order_mocker(agreement_update_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    first = await (await order_event_handler.get_processor(object_id=order_id)).process()
    purchase_order_mocker(new_user=False, provision=False)
    retry = await (await order_event_handler.get_processor(object_id=order_id)).process()

    assert first.status is ProcessingStatus.RESCHEDULE
    assert retry.status is ProcessingStatus.COMPLETE
    [entry] = await fetch_operation_entries(f"order:{order_id}")
    assert entry.status == ActivityStatus.COMPLETED
    notes = [note.message for note in entry.notes]
    assert notes[:2] == [
        "FinOps for Cloud user employee-id (pl@example.com) created.",
        "FinOps for Cloud organization OPT-ORG-0001 created.",
    ]
    assert notes[2].startswith("Attempt failed: HTTPStatusError: Server error '500")
    assert notes[3] == "FinOps for Cloud user employee-id (pl@example.com) already exists."
    assert notes[4].startswith(f"Agreement {purchase_order['agreement']['id']} linked")
    assert notes[5:] == ["Completed."]


@freeze_time("2024-12-01")
async def test_purchase_order_retry_does_not_duplicate_the_records_of_the_failed_attempt(
    purchase_order: dict[str, Any],
    purchase_order_mocker: OrderMocker,
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """The retry of a purchase finds the client account and the linked organization of the
    failed attempt and records nothing more."""
    order_id = purchase_order["id"]
    purchase_order_mocker(agreement_update_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    await (await order_event_handler.get_processor(object_id=order_id)).process()
    purchase_order_mocker(new_user=False, provision=False)
    await (await order_event_handler.get_processor(object_id=order_id)).process()

    [entry] = await fetch_operation_entries(f"order:{order_id}")
    assert change_kinds(entry) == PROVISIONING_CHANGES


@freeze_time("2025-06-01")
async def test_purchase_order_failed_past_its_due_date_abandons_its_entry(
    purchase_order: dict[str, Any],
    purchase_order_mocker: OrderMocker,
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
) -> None:
    """A purchase that fails past its due date is failed in Marketplace, and its entry is
    abandoned with the reason as its last note and the records it had."""
    # The factory order carries a due date of 2025-01-01.
    order_id = purchase_order["id"]
    purchase_order_mocker(agreement_update_status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/fail",
        match_json={"statusNotes": ERR_DUE_DATE_IS_REACHED.to_dict(due_date="2025-01-01")},
        json=purchase_order,
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Error"
    [entry] = await fetch_operation_entries(f"order:{order_id}")
    assert entry.status == ActivityStatus.ABANDONED
    assert entry.notes[-1].message == "Order failed in Marketplace: Due date is reached 2025-01-01"
    assert change_kinds(entry) == PROVISIONING_CHANGES


async def test_purchase_order_failed_without_a_due_date_abandons_its_entry(
    purchase_order: dict[str, Any],
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
) -> None:
    """A purchase with no due date that fails is failed in Marketplace, and its entry is
    abandoned with that reason."""
    purchase_order = set_due_date(purchase_order, None)
    order_id = purchase_order["id"]
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/fail",
        match_json={"statusNotes": ERR_DUE_DATE_NOT_SET.to_dict()},
        json=purchase_order,
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    result = await processor.process()

    assert result.status is ProcessingStatus.CANCEL
    [entry] = await fetch_operation_entries(f"order:{order_id}")
    assert entry.status == ActivityStatus.ABANDONED
    assert entry.notes[-1].message == (
        "Order failed in Marketplace: No due date fulfillment parameter found."
    )


@pytest.mark.parametrize("earlier_attempt", [False, True])
async def test_purchase_order_moved_to_querying_is_noted_on_its_in_progress_entry(
    purchase_order: dict[str, Any],
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    earlier_attempt: bool,
) -> None:
    """An order moved to Querying notes why on the in-progress entry of the order, the one
    of an earlier attempt or a new one, which waits for the customer."""
    order_id = purchase_order["id"]
    key = f"order:{order_id}"
    earlier_entry_ids = []
    if earlier_attempt:
        operation = ActivityOperation(
            db_session,
            key=key,
            action="organization.provisioned",
            message=f"Provisioning FinOps for Cloud for purchase order {order_id}.",
            actor_id=APP_ACTOR_ID,
        )
        async with operation.attempt():
            pass
        earlier_entry_ids = [entry.id for entry in await fetch_operation_entries(key)]
    get_ordering_parameter(purchase_order, PARAM_ORGANIZATION_NAME)["value"] = None
    queried_order = copy.deepcopy(purchase_order)
    queried_parameter = get_ordering_parameter(queried_order, PARAM_ORGANIZATION_NAME)
    queried_parameter["error"] = ERR_ORGANIZATION_NAME.to_dict()
    queried_parameter["constraints"] = {"hidden": False, "required": True}
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{test_settings.mpt_product_id}"
            f"/templates?limit={test_settings.mpt_api_rows_per_page}&offset=0"
        ),
        json={
            "data": [
                {"id": "TPL-0003", "type": QUERYING_TEMPLATE_TYPE, "name": None, "default": True}
            ],
            "$meta": {"pagination": {"total": 1}},
        },
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_json={"parameters": queried_order["parameters"]},
        json=queried_order,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/query",
        match_json={"template": {"id": "TPL-0003"}},
        json={**queried_order, "status": "Querying"},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    result = await processor.process()

    assert result.status is ProcessingStatus.SKIP
    [entry] = await fetch_operation_entries(key)
    assert entry.status == ActivityStatus.IN_PROGRESS
    assert entry.notes[-1].message == "Order moved to Querying: Organization name is required."
    if earlier_attempt:
        assert [entry.id] == earlier_entry_ids


async def test_create_order_subscription_notes_each_subscription_created(
    order_factory: OrderFactory,
    organization_factory: ModelFactory[Organization],
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
) -> None:
    """Each subscription created in Marketplace for an order line is noted on the entry of
    the order."""
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id=test_settings.mpt_product_id,
        product_name="SoftwareOne FinOps for Cloud",
        subscriptions=[],
    )
    line = order["lines"][0]
    organization = await organization_factory(operations_external_id=order["agreement"]["id"])
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=order,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order['id']}/subscriptions",
        match_json={
            "name": f"Subscription for {line['item']['name']}",
            "parameters": {},
            "externalIds": {"vendor": organization.id},
            "lines": [{"id": line["id"]}],
        },
        json={"id": "SUB-9999-0001"},
    )
    processor = await order_event_handler.get_processor(object_id=order["id"])

    await processor.create_order_subscription(organization)

    [entry] = await fetch_operation_entries(f"order:{order['id']}")
    assert [note.message for note in entry.notes] == [
        f"Marketplace subscription SUB-9999-0001 created for order line {line['id']}."
    ]


# -- termination ----------------------------------------------------------------------


async def test_termination_order_is_one_completed_termination_entry_by_the_application(
    terminate_order: dict[str, Any],
    organization_to_terminate: Organization,
    termination_order_mocker: OrderMocker,
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """A termination is one completed `organization.terminated` entry by the application,
    noting the suspension in FinOps for Cloud and its completion."""
    order_id = terminate_order["id"]
    termination_order_mocker(organization_to_terminate)
    processor = await order_event_handler.get_processor(object_id=order_id)

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    [entry] = await fetch_operation_entries(f"order:{order_id}")
    assert entry.action == "organization.terminated"
    assert entry.status == ActivityStatus.COMPLETED
    assert entry.recorded_by_id == APP_ACTOR_ID
    assert entry.message == (
        f"FinOps for Cloud service terminated for organization 'ACME Inc' "
        f"({organization_to_terminate.id}), agreement {terminate_order['agreement']['id']}. "
        f"Termination order {order_id}."
    )
    assert [note.message for note in entry.notes] == [
        "FinOps for Cloud organization OPT-ORG-0001 suspended.",
        "Completed.",
    ]


async def test_termination_order_entry_records_the_organization_entitlements_and_feedback(
    terminate_order: dict[str, Any],
    organization_to_terminate: Organization,
    termination_order_mocker: OrderMocker,
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """The entry of a termination records the organization terminated, its entitlements
    terminated and re-issued, and the termination feedback."""
    termination_order_mocker(organization_to_terminate)
    processor = await order_event_handler.get_processor(object_id=terminate_order["id"])

    await processor.process()

    [entry] = await fetch_operation_entries(f"order:{terminate_order['id']}")
    assert sorted(change_kinds(entry)) == TERMINATION_CHANGES


@freeze_time("2024-12-01")
async def test_termination_order_retry_completes_its_entry_without_duplicating_records(
    terminate_order: dict[str, Any],
    organization_to_terminate: Organization,
    termination_order_mocker: OrderMocker,
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """A termination retried after its completion failed in Marketplace completes the same
    entry, which notes the failure and keeps the records of the first attempt only."""
    order_id = terminate_order["id"]
    termination_order_mocker(
        organization_to_terminate, complete_status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    first = await (await order_event_handler.get_processor(object_id=order_id)).process()
    termination_order_mocker(organization_to_terminate, disabled=True)
    retry = await (await order_event_handler.get_processor(object_id=order_id)).process()

    assert first.status is ProcessingStatus.RESCHEDULE
    assert retry.status is ProcessingStatus.COMPLETE
    [entry] = await fetch_operation_entries(f"order:{order_id}")
    assert entry.status == ActivityStatus.COMPLETED
    assert sorted(change_kinds(entry)) == TERMINATION_CHANGES
    notes = [note.message for note in entry.notes]
    assert notes[0] == "FinOps for Cloud organization OPT-ORG-0001 suspended."
    assert notes[1].startswith("Attempt failed: HTTPStatusError: Server error '500")
    assert notes[2:] == ["Completed."]


async def test_termination_order_of_a_missing_organization_abandons_its_entry(
    terminate_order: dict[str, Any],
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
) -> None:
    """A termination whose agreement points at an unknown organization is cancelled, and
    its entry abandoned with the reason."""
    order_id = terminate_order["id"]
    agreement_id = terminate_order["agreement"]["id"]
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=terminate_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        json={"externalIds": {"client": "", "vendor": "FORG-8077-2461-7285"}},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    result = await processor.process()

    assert result.status is ProcessingStatus.CANCEL
    [entry] = await fetch_operation_entries(f"order:{order_id}")
    assert entry.status == ActivityStatus.ABANDONED
    assert entry.notes[-1].message == result.message


async def test_termination_order_of_an_unlinked_organization_abandons_its_entry(
    terminate_order: dict[str, Any],
    organization_factory: ModelFactory[Organization],
    order_event_handler: OrderEventHandler,
    fetch_operation_entries: ActivityLogFetcher,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
) -> None:
    """A termination of an organization with no FinOps for Cloud organization is
    cancelled, and its entry abandoned with the reason."""
    order_id = terminate_order["id"]
    agreement_id = terminate_order["agreement"]["id"]
    organization = await organization_factory(operations_external_id=agreement_id)
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=terminate_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        json={"externalIds": {"client": "", "vendor": organization.id}},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    result = await processor.process()

    assert result.status is ProcessingStatus.CANCEL
    [entry] = await fetch_operation_entries(f"order:{order_id}")
    assert entry.status == ActivityStatus.ABANDONED
    assert entry.notes[-1].message == (
        f"The organization {organization.id} is not linked to a FinOps for Cloud Organization."
    )


# -- change ---------------------------------------------------------------------------


async def test_change_order_records_nothing(
    change_order: dict[str, Any],
    order_event_handler: OrderEventHandler,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
) -> None:
    """A change order, failed in Marketplace as unsupported, writes no activity log entry."""
    order_id = change_order["id"]
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=change_order,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/fail",
        match_json={"statusNotes": ERR_ORDER_TYPE_NOT_SUPPORTED.to_dict(order_type="Change")},
        json=change_order,
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert await db_session.scalar(select(func.count()).select_from(ActivityLog)) == 0


async def test_change_order_processor_has_no_operation(
    change_order: dict[str, Any],
    order_event_handler: OrderEventHandler,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
) -> None:
    """The processor of a change order refuses to give an activity operation."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{change_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=change_order,
    )
    processor = await order_event_handler.get_processor(object_id=change_order["id"])

    with pytest.raises(RuntimeError, match="does not record its orders"):
        _ = processor.operation


@freeze_time("2025-06-01")
async def test_change_order_failed_past_its_due_date_records_nothing(
    change_order: dict[str, Any],
    order_event_handler: OrderEventHandler,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
) -> None:
    """A change order that cannot be failed as unsupported, and is failed past its due date
    instead, writes no activity log entry."""
    # The factory order carries a due date of 2025-01-01.
    order_id = change_order["id"]
    fail_url = f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/fail"
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=change_order,
    )
    httpx_mock.add_response(
        method="POST",
        url=fail_url,
        match_json={"statusNotes": ERR_ORDER_TYPE_NOT_SUPPORTED.to_dict(order_type="Change")},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    httpx_mock.add_response(
        method="POST",
        url=fail_url,
        match_json={"statusNotes": ERR_DUE_DATE_IS_REACHED.to_dict(due_date="2025-01-01")},
        json=change_order,
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Error"
    assert await db_session.scalar(select(func.count()).select_from(ActivityLog)) == 0
