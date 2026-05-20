import logging
from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter

from app import Settings
from app.api_clients.mpt import MPTClient
from app.db.handlers import OrganizationHandler
from app.dependencies.api_clients import (
    APIModifierClient,
    ExtensionClient,
    InstallationClient,
    OptscaleAuthClient,
)
from app.dependencies.core import AppSettings, ExtensionContext
from app.dependencies.db import OrganizationRepository
from app.order_fulfilment.constants import (
    MPT_ORDER_STATUS_PROCESSING,
    MPT_ORDER_STATUS_QUERYING,
)
from app.order_fulfilment.error import ERR_DUE_DATE_IS_REACHED
from app.order_fulfilment.helpers import (
    check_order_parameters,
    create_employee,
    create_order_subscription,
    get_or_create_organization,
    get_parameter_updates,
    start_processing_order_template,
)
from app.order_fulfilment.parameters import set_fulfillment_parameter
from app.parameters import (
    get_due_date,
)
from app.schemas.core import Event, EventResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events")


async def _start_task_and_get_order(
    *,
    task_id: str,
    order_id: str,
    ext_ctx: ExtensionContext,
    ext_client: MPTClient,
    client: MPTClient,
) -> dict[str, Any]:
    """Start task execution and fetch the order payload."""
    logger.info("Changing task %s status to Processing", task_id)
    await ext_client.start_task(task_id, ext_ctx.instance_id)
    return await client.get_order(order_id)


async def _validate_and_move_to_querying_if_needed(
    *,
    order: dict[str, Any],
    product_id: str,
    ext_client: ExtensionClient,
) -> tuple[dict[str, Any], bool]:
    """
    Validate ordering params and move order back to Querying if invalid.
    """
    order_with_validation_errors, validation_succeeded = check_order_parameters(order)
    order_id = order["id"]
    if not validation_succeeded:
        template = await ext_client.get_product_template_or_default(
            product_id=product_id,
            status=MPT_ORDER_STATUS_QUERYING,
        )
        # Persist validation errors before moving the order back to Query.
        await ext_client.update_order(
            order_id=order_id,
            parameters=order_with_validation_errors["parameters"],
        )
        querying_order = await ext_client.set_status_to_querying(
            order_id=order_id, payload=template
        )
        logger.info("%s: ordering parameters are invalid, move to querying", querying_order["id"])
        return order_with_validation_errors, False
    return order, True


@router.post("/commerce/orders")
async def process_order(
    event: Event,
    settings: AppSettings,
    ext_ctx: ExtensionContext,
    client: InstallationClient,
    ext_client: ExtensionClient,
    organization_repo: OrganizationRepository,
    optscale_auth_client: OptscaleAuthClient,
    api_modifier_client: APIModifierClient,
) -> EventResponse:
    """
        try:
        fetch order is in progress
        set task in progress
        get or create organization
        get or create user
        complete order
        complete task
        return ok
    except:
      if now < due_date:
            reschedule task
            return reschedule
      else:
          fail order
          OK task con descrizione fail raggiunta la due date
          return ok e scriviamo nel task che l'ordine e' fallito.
    """
    # settings = get_settings()
    logger.info(f"--------PAYLOAD {event}")
    # return EventResponse.cancel()

    order_id = event.object.id
    if event.task is None:
        logger.error("Received order event %s without task information", event.id)
        return EventResponse.cancel()

    task_id = event.task.id
    product_id = settings.mpt_product_id
    order: dict[str, Any] = {}

    try:
        # 1. Set task to Processing & fetch order
        order = await _start_task_and_get_order(
            task_id=task_id,
            order_id=order_id,
            ext_client=ext_client,
            ext_ctx=ext_ctx,
            client=client,
        )

        # 2. Check status — skip if not processing
        if order["status"] != MPT_ORDER_STATUS_PROCESSING:
            await ext_client.complete_task(task_id)
            return EventResponse.ok()

        # 3. setting fulfillment's parameters
        order = await _apply_fulfillment_defaults_if_needed(
            ext_client=ext_client,
            order=order,
            settings=settings,
        )
        # check order parameters & move order to Query if parameters are invalid
        order, is_valid = await _validate_and_move_to_querying_if_needed(
            order=order,
            ext_client=ext_client,
            product_id=product_id,
        )
        if not is_valid:
            await ext_client.complete_task(task_id)
            return EventResponse.ok()
        # 6 Start Order 'happy path' processing

        return await _process_order_happy_path(
            api_modifier_client=api_modifier_client,
            ext_client=ext_client,
            optscale_auth_client=optscale_auth_client,
            order=order,
            order_id=order_id,
            organization_repo=organization_repo,
            product_id=product_id,
            task_id=task_id,
        )

    except Exception as exc:
        return await _handle_exception(exc, ext_client, order, order_id, task_id)


async def _handle_exception(
    exc: Exception, ext_client: MPTClient, order: dict[str, Any], order_id: str, task_id: str
) -> EventResponse:
    logger.exception("Unexpected error processing order %s: %s", order_id, exc)
    due_date: date | None = get_due_date(order) if order else None
    if due_date is None:
        try:
            await ext_client.fail_order(
                order_id=order_id, payload={"description": "due date is not set"}
            )

            return EventResponse.cancel()
        except Exception as inn_exc:
            logger.exception(
                "Failed to fail order %s after missing due date: %s", order_id, inn_exc
            )
            return EventResponse.cancel()
    task = await ext_client.get_task(task_id)
    description = task.get("description", "")
    now = datetime.now(UTC).date()
    error_message = str(exc)
    if due_date and now < due_date:
        await ext_client.reschedule_task(
            task_id,
            payload={"description": f"{description} - {now.isoformat()} - {error_message}"},
        )
        return EventResponse.reschedule(seconds=300)
    logger.info(
        f"Switch order {order_id} to failed status. "
        f"Reason: due date is reached {due_date.strftime('%Y-%m-%d')}"
    )
    await ext_client.fail_order(
        order_id=order_id,
        payload=ERR_DUE_DATE_IS_REACHED.to_dict(due_date=due_date.strftime("%Y-%m-%d")),
    )

    await ext_client.complete_task(
        task_id,
        payload={"description": f"{description} - {now.isoformat()} - {error_message}"},
    )
    return EventResponse.ok()


async def _process_order_happy_path(
    *,
    api_modifier_client: APIModifierClient,
    ext_client: MPTClient,
    optscale_auth_client: OptscaleAuthClient,
    order: dict[str, Any],
    order_id: str,
    organization_repo: OrganizationHandler,
    product_id: str,
    task_id: str,
) -> EventResponse:
    order = await start_processing_order_template(ext_client, order, product_id)
    logger.info(f"-------------Processing order {order_id}")
    # 8 create employee
    order = await create_employee(api_modifier_client, ext_client, optscale_auth_client, order)

    # 9 get or create organization

    organization = await get_or_create_organization(ext_client, order, organization_repo)

    # Create subscription
    await create_order_subscription(ext_client, order, organization)

    # Complete order
    await ext_client.complete_order(order_id=order_id)
    # 7. Complete task
    await ext_client.complete_task(task_id)
    return EventResponse.ok()


async def _apply_fulfillment_defaults_if_needed(
    ext_client: MPTClient, order: dict[str, Any], settings: Settings
) -> dict[str, Any]:
    updated_parameters = get_parameter_updates(order, settings)
    if updated_parameters:
        for param_name, param_value in updated_parameters.items():
            order = set_fulfillment_parameter(
                order=order,
                parameter=param_name,
                value=param_value,
            )
        order = await ext_client.update_order(order_id=order["id"], parameters=order["parameters"])
        logger.info("%s: updating fulfillment parameters", order["id"])
    return order
