import copy
import enum
import logging
import secrets
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from app.api_clients.mpt import MPTClient
from app.api_clients.optscale import UserDoesNotExist
from app.db.models import Organization
from app.dependencies.api_clients import (
    APIModifierClient,
    InstallationClient,
    OptscaleAuthClient,
    OptscaleClient,
)
from app.dependencies.core import AppSettings
from app.dependencies.db import EntitlementRepository, OrganizationRepository
from app.fulfilment.constants import (
    COMPLETED_TEMPLATE_TYPE,
    MPT_ORDER_STATUS_PROCESSING,
    ORDER_TYPE_CHANGE,
    ORDER_TYPE_PURCHASE,
    ORDER_TYPE_TERMINATE,
    PROCESSING_TEMPLATE_TYPE,
    PURCHASE_EXISTING_TEMPLATE_NAME,
    PURCHASE_TEMPLATE_NAME,
    QUERYING_TEMPLATE_TYPE,
    TERMINATE_TEMPLATE_NAME,
)
from app.fulfilment.error import (
    ERR_DUE_DATE_IS_REACHED,
    ERR_DUE_DATE_NOT_SET,
    ERR_ORDER_TYPE_NOT_SUPPORTED,
)
from app.fulfilment.exceptions import (
    OrderMovedToQuery,
    OrderNotValidError,
    UnsupportedOrderTypeError,
)
from app.fulfilment.parameters import (
    check_order_parameters,
    get_billing_defaults_updates,
    get_due_date_update,
)
from app.fulfilment.subscriptions import get_subscription_by_line_and_item_id
from app.parameters import (
    PARAM_ADMIN_CONTACT,
    PARAM_CURRENCY,
    PARAM_DUE_DATE,
    PARAM_IS_NEW_USER,
    PARAM_ORGANIZATION_NAME,
    get_due_date,
    get_fulfillment_parameter,
    get_ordering_parameter,
    set_is_new_user,
)

logger = logging.getLogger(__name__)


class ProcessingStatus(enum.StrEnum):
    COMPLETE = "Complete"
    RESCHEDULE = "Reschedule"
    CANCEL = "Cancel"
    SKIP = "Skip"


@dataclass
class ProcessingResult:
    status: ProcessingStatus
    severity: str | None = None
    message: str | None = None


class OrderProcessor(ABC):
    def __init__(
        self,
        api_modifier_client: APIModifierClient,
        client: InstallationClient,
        ext_client: MPTClient,
        optscale_auth_client: OptscaleAuthClient,
        optscale_client: OptscaleClient,
        organization_repo: OrganizationRepository,
        entitlement_repo: EntitlementRepository,
        settings: AppSettings,
        order: dict[str, Any],
    ):
        self.api_modifier_client = api_modifier_client
        self.client = client
        self.ext_client = ext_client
        self.optscale_auth_client = optscale_auth_client
        self.optscale_client = optscale_client
        self.organization_repo = organization_repo
        self.entitlement_repo = entitlement_repo
        self.settings = settings
        self.order = order
        self.template_cache = {}

    def set_template(self, order: dict, template_id: str | None) -> dict:
        """Return a copy of the order with the provided template assigned."""
        if not template_id:
            raise ValueError("Template id is required")
        updated_order = copy.deepcopy(order)
        try:
            updated_order["template"]["id"] = template_id
            self.order = updated_order
            return self.order
        except KeyError as exc:
            logger.error(
                "%s: order is malformed, missing key %s; template_id=%s",
                self.order.get("id", "<unknown>"),
                exc,
                template_id,
            )
            raise KeyError(f"Order is malformed: missing key {exc}") from exc

    async def get_product_template_id(
        self, template_type: str, template_name: str | None
    ) -> Any | None:
        product_id = self.settings.mpt_product_id
        if not self.template_cache:
            logger.info("Initializing template cache for product %s", product_id)
            await self.fetch_product_templates(product_id)
            logger.info("Template cache initialized with %d entries", len(self.template_cache))
        logger.info("Fetching template %s", template_name)
        template_id = self.template_cache.get(
            (template_type, template_name)
        ) or self.template_cache.get((template_type, None))
        if template_id is None:
            raise OrderNotValidError(f"Product {product_id} has no template type {template_type}.")
        return template_id

    async def fetch_product_templates(self, product_id: str) -> None:
        async for template in self.ext_client.get_templates_by_product_id(product_id=product_id):
            template_id = template["id"]
            template_type = template["type"]
            template_name = template["name"] if not template["default"] else None
            self.template_cache[(template_type, template_name)] = template_id
            logger.debug("Cached template %s (%s, %s)", template_id, template_type, template_name)

    async def validate_and_move_to_querying_if_needed(self) -> bool:
        """
        Validate ordering params and move order back to Query if invalid.
        """
        order_with_validation_errors, validation_succeeded = check_order_parameters(
            order=self.order
        )
        order_id = self.order["id"]
        if not validation_succeeded:
            template_id = await self.get_product_template_id(QUERYING_TEMPLATE_TYPE, None)
            await self.ext_client.update_order(
                order_id=order_id,
                parameters=order_with_validation_errors["parameters"],
            )
            querying_order = await self.ext_client.set_status_to_querying(
                order_id=order_id, payload={"template": {"id": template_id}}
            )
            querying_order["parameters"] = order_with_validation_errors["parameters"]
            logger.info(
                "%s: ordering parameters are invalid, move to querying", querying_order["id"]
            )
            return False
        return True

    async def validate_order_status(self) -> None:
        if self.order["status"] != MPT_ORDER_STATUS_PROCESSING:
            raise OrderNotValidError(f"Order {self.order['id']} is not in Processing status")

    async def validate_order(self) -> None:
        await self.validate_order_status()
        is_valid = await self.validate_and_move_to_querying_if_needed()
        if not is_valid:
            raise OrderMovedToQuery(f"Order {self.order['id']} is not valid")

    async def _store_order_parameters_updates(
        self, updated_parameters: dict[str, Any]
    ) -> dict[str, Any]:
        if not updated_parameters:
            return self.order
        else:
            order = copy.deepcopy(self.order)
            for param_name, param_value in updated_parameters.items():
                param = get_fulfillment_parameter(order, param_name)
                if not param:
                    raise OrderNotValidError(
                        f"Order {self.order['id']} has not fulfillment parameter {param_name}"
                    )
                param["value"] = param_value
            self.order = await self.ext_client.update_order(
                order_id=order["id"], parameters=order["parameters"]
            )
            logger.info("%s: updating fulfillment parameters", self.order["id"])
            return self.order

    async def apply_fulfillment_defaults(self) -> dict[str, Any]:
        """
        Fill in the fulfillment parameters and persist them.
        Computes defaults for `dueDate` (today + `due_date_days`),
        `billedPercentage`,`trialStartDate` and `trialEndDate`,
        skipping any parameter that already carries a value.

        :return:
        the updated order as returned by the marketplace, or the current
        order unchanged when every parameter was already set.
        """
        updates_parameters = {
            **get_due_date_update(self.order, self.settings),
            **get_billing_defaults_updates(self.order, self.settings),
        }
        return await self._store_order_parameters_updates(updates_parameters)

    async def get_or_create_organization(
        self,
        employee_id: str,
    ) -> Organization:
        """Get or create the organization and link it back to the marketplace agreement."""
        agreement_id = self.order["agreement"]["id"]
        agreement = await self.ext_client.get_agreement(agreement_id, select=["authorization"])

        org_name = get_ordering_parameter(self.order, PARAM_ORGANIZATION_NAME)["value"]
        org_currency = get_ordering_parameter(self.order, PARAM_CURRENCY)["value"]
        billing_currency = agreement["authorization"]["currency"]  # marketplace billing currency

        organization, created = await self.organization_repo.get_or_create(
            operations_external_id=agreement_id,
            defaults={
                "name": org_name,
                "currency": org_currency,
                "billing_currency": billing_currency,
            },
        )

        if created or not organization.linked_organization_id:
            organization_on_optscale = await self.api_modifier_client.create_organization(
                org_name=org_name, user_id=employee_id, currency=org_currency
            )
            optscale_organization = organization_on_optscale.json()
            logger.info("Organization on OptScale created with id %s ", optscale_organization["id"])
            await self.organization_repo.update(
                organization.id,
                {
                    "linked_organization_id": optscale_organization["id"],
                },
            )
            await self.ext_client.update_agreement(
                agreement_id,
                externalIds={"vendor": organization.id},
            )

            logger.info(
                "%s: Updating organization %s with external id to %s ",
                self.order["id"],
                organization.id,
                optscale_organization["id"],
            )
            logger.info("Organization created with id %s ", organization.id)
        else:
            logger.info("Organization already exists with id %s ", organization.id)

        return organization

    async def create_employee(self) -> tuple[str, str]:
        """Resolve or create the admin user and persist the `isNewUser` fulfillment flag."""
        administrator = get_ordering_parameter(self.order, PARAM_ADMIN_CONTACT)["value"]
        email = administrator["email"]

        try:
            response = await self.optscale_auth_client.get_existing_user_info(email)
            response_json = response.json()
            employee_id = response_json["user_info"]["id"]
            is_new = False
            logger.info("Employee exists with id %s for order %s", employee_id, self.order["id"])
        except UserDoesNotExist:
            response = await self.api_modifier_client.create_user(
                email=email,
                display_name=f"{administrator['firstName']} {administrator['lastName']}",
                password=secrets.token_urlsafe(128),
            )
            response_json = response.json()
            employee_id = response_json["id"]
            is_new = True
            logger.info("Employee created with id %s for order %s", employee_id, self.order["id"])
        updated_order = set_is_new_user(self.order, is_new=is_new)
        self.order = await self.ext_client.update_order(
            self.order["id"],
            parameters=updated_order["parameters"],
        )
        logger.debug("Updated orders %s %s ", updated_order["parameters"], self.order["parameters"])
        return employee_id, email

    async def create_order_subscription(self, organization: Organization) -> None:
        """Create missing subscriptions for each order line and bind them to the organization."""
        for line in self.order["lines"]:
            order_subscription = get_subscription_by_line_and_item_id(
                self.order["subscriptions"],
                line["item"]["id"],
                line["id"],
            )
            if not order_subscription:
                subscription = {
                    "name": f"Subscription for {line['item']['name']}",
                    "parameters": {},
                    "externalIds": {"vendor": organization.id},
                    "lines": [
                        {
                            "id": line["id"],
                        },
                    ],
                }
                subscription = await self.ext_client.create_subscription(
                    order_id=self.order["id"],
                    subscription=subscription,
                )
                logger.info(
                    "%s: subscription %s (%s) created",
                    self.order["id"],
                    line["id"],
                    subscription["id"],
                )

    async def handle_processing_failure(self, exc: Exception) -> ProcessingResult:
        due_date: date | None = get_due_date(self.order)
        if due_date is None:
            # No due date to retry against: fail the order and cancel.
            await self.ext_client.fail_order(
                order_id=self.order["id"],
                payload={"statusNotes": ERR_DUE_DATE_NOT_SET.to_dict()},
            )
            return ProcessingResult(
                status=ProcessingStatus.CANCEL,
                severity="Error",
                message=ERR_DUE_DATE_NOT_SET.message,
            )
        now = datetime.now(UTC).date()
        if now < due_date:
            # Still within the due date window: retry later.
            return ProcessingResult(
                status=ProcessingStatus.RESCHEDULE,
                severity="Warning",
                message=f"An error occurred while processing the order {self.order['id']}: "
                f"{traceback.format_exc()}",
            )
        # Due date reached: fail the order and let the task complete.
        status_notes = ERR_DUE_DATE_IS_REACHED.to_dict(due_date=due_date.strftime("%Y-%m-%d"))
        await self.ext_client.fail_order(
            order_id=self.order["id"],
            payload={"statusNotes": status_notes},
        )
        return ProcessingResult(
            status=ProcessingStatus.COMPLETE,
            severity="Error",
            message=status_notes["message"],
        )

    @abstractmethod
    async def process(self) -> ProcessingResult:
        raise NotImplementedError()


class PurchaseOrderProcessor(OrderProcessor):
    async def send_reset_password(self, employee_email: str, is_new: bool):
        if is_new:
            try:
                await self.optscale_client.reset_password(employee_email)
                logger.info("Employee %s password reset sent", employee_email)

            except Exception:
                logger.exception("Failed to reset password")
        else:
            logger.info("No need to send reset password for %s", employee_email)

    async def get_complete_template(self, is_new: bool) -> str | None:
        if is_new:
            template_name = PURCHASE_TEMPLATE_NAME
        else:
            template_name = PURCHASE_EXISTING_TEMPLATE_NAME

        template_id = await self.get_product_template_id(COMPLETED_TEMPLATE_TYPE, template_name)
        return template_id

    async def set_processing_order_template(self) -> dict:
        """Ensure the order uses the processing template expected for purchase flow."""
        template_id = await self.get_product_template_id(
            PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME
        )
        logger.info("Processing order template: %s", template_id)
        current_template_id = self.order.get("template", {}).get("id")
        if template_id != current_template_id:
            order = self.set_template(order=self.order, template_id=template_id)
            order = await self.ext_client.update_order(
                order_id=order["id"],
                template={"id": template_id},
            )
            self.order = order
            logger.info(
                "%s: processing template set to %s (%s)",
                order["id"],
                PURCHASE_TEMPLATE_NAME,
                template_id,
            )

        logger.info("%s: processing template is ok, continue", self.order["id"])
        return self.order

    async def process(self) -> ProcessingResult:
        try:
            await self.validate_order()
            await self.apply_fulfillment_defaults()
            await self.set_processing_order_template()
            employee_id, employee_email = await self.create_employee()
            organization = await self.get_or_create_organization(employee_id)

            await self.create_order_subscription(organization)
            is_new_user_param = get_fulfillment_parameter(self.order, PARAM_IS_NEW_USER)
            is_new = is_new_user_param.get("value") == ["Yes"]
            template_id = await self.get_complete_template(is_new)
            await self.ext_client.complete_order(
                order_id=self.order["id"],
                payload={
                    "template": {"id": template_id},
                    "parameters": {"fulfillment": [{"externalId": PARAM_DUE_DATE, "value": None}]},
                },
            )

            await self.send_reset_password(employee_email, is_new)
            logger.info("Order %s has been completed", self.order["id"])
            return ProcessingResult(
                status=ProcessingStatus.COMPLETE,
                message=f"Order {self.order['id']} has been successfully processed",
            )
        except Exception as exc:
            logger.exception("%s: Purchase Order processing failed.", self.order["id"])
            if isinstance(exc, OrderMovedToQuery | OrderNotValidError):
                return ProcessingResult(
                    status=ProcessingStatus.SKIP,
                    severity="Info",
                    message="Order parameters are missing or invalid. Order Skipped.",
                )

            return await self.handle_processing_failure(exc)


class ChangeOrderProcessor(OrderProcessor):
    async def process(self) -> ProcessingResult:
        try:
            await self.ext_client.fail_order(
                order_id=self.order["id"],
                payload={
                    "statusNotes": ERR_ORDER_TYPE_NOT_SUPPORTED.to_dict(
                        order_type=self.order["type"]
                    )
                },
            )

            return ProcessingResult(
                status=ProcessingStatus.COMPLETE,
                severity="Warning",
                message="Change orders are not supported.",
            )
        except Exception as exc:
            logger.exception("%s: Change Order processing failed.", self.order["id"])
            return await self.handle_processing_failure(exc)


class TerminateOrderProcessor(OrderProcessor):
    async def process(self) -> ProcessingResult:
        try:
            await self.validate_order_status()
            await self._store_order_parameters_updates(
                get_due_date_update(self.order, self.settings)
            )

            agreement_id = self.order["agreement"]["id"]
            agreement = await self.ext_client.get_agreement(agreement_id)
            organization_id = agreement.get("externalIds", {}).get("vendor")
            organization = await self.organization_repo.first(
                where_clauses=[
                    Organization.id == organization_id,
                ]
            )
            if organization is None:
                return ProcessingResult(
                    status=ProcessingStatus.CANCEL,
                    severity="Error",
                    message=f"The organization {organization_id} linked to agreement {agreement_id}"
                    f" was not found.",
                )
            if not organization.linked_organization_id:
                return ProcessingResult(
                    status=ProcessingStatus.CANCEL,
                    severity="Error",
                    message=f"The organization {organization_id} is not linked to a FinOps "
                    f"for Cloud Organization.",
                )
            optscale_org_id = organization.linked_organization_id

            response = await self.optscale_client.get_organization(optscale_org_id)
            optscale_organization = response.json()
            is_disabled = optscale_organization["disabled"]
            template_id = await self.get_product_template_id(
                COMPLETED_TEMPLATE_TYPE, TERMINATE_TEMPLATE_NAME
            )
            if is_disabled:
                severity = "Warning"
                message = f"The Organization {organization_id} was already terminated."

            else:
                await self.optscale_client.suspend_organization(optscale_org_id)

                await self.organization_repo.terminate(organization)
                await self.entitlement_repo.terminate_active_for_organization(organization)

                severity = "Info"
                message = f"The Organization {organization_id} was successfully suspended."

            await self.ext_client.complete_order(
                order_id=self.order["id"],
                payload={
                    "template": {"id": template_id},
                    "parameters": {"fulfillment": [{"externalId": PARAM_DUE_DATE, "value": None}]},
                },
            )
            return ProcessingResult(
                status=ProcessingStatus.COMPLETE,
                severity=severity,
                message=message,
            )
        except Exception as exc:
            logger.exception("%s: Terminate processing failed.", self.order["id"])
            return await self.handle_processing_failure(exc)


PROCESSOR_BY_TYPE: dict[str, type["OrderProcessor"]] = {
    ORDER_TYPE_PURCHASE: PurchaseOrderProcessor,
    ORDER_TYPE_CHANGE: ChangeOrderProcessor,
    ORDER_TYPE_TERMINATE: TerminateOrderProcessor,
}


class OrderProcessorFactory:
    def __init__(
        self,
        api_modifier_client: APIModifierClient,
        client: InstallationClient,
        ext_client: MPTClient,
        optscale_auth_client: OptscaleAuthClient,
        optscale_client: OptscaleClient,
        organization_repo: OrganizationRepository,
        entitlement_repo: EntitlementRepository,
        settings: AppSettings,
    ):
        self.api_modifier_client = api_modifier_client
        self.client = client
        self.ext_client = ext_client
        self.optscale_auth_client = optscale_auth_client
        self.optscale_client = optscale_client
        self.organization_repo = organization_repo
        self.entitlement_repo = entitlement_repo
        self.settings = settings

    async def get_order_type_processor(self, order_id: str) -> OrderProcessor:
        order = await self.client.get_order(order_id, select=["subscriptions.lines"])
        order_type = order["type"]
        logger.info("ORDER TYPE: %s", order_type)
        processor_cls = PROCESSOR_BY_TYPE.get(order_type)
        if processor_cls is None:
            logger.warning("%s The order type %s is not supported.", order_type, order_type)
            raise UnsupportedOrderTypeError(order_type)
        return processor_cls(
            api_modifier_client=self.api_modifier_client,
            client=self.client,
            ext_client=self.ext_client,
            optscale_auth_client=self.optscale_auth_client,
            optscale_client=self.optscale_client,
            organization_repo=self.organization_repo,
            entitlement_repo=self.entitlement_repo,
            order=order,
            settings=self.settings,
        )
