import copy
import enum
import logging
import secrets
from datetime import date
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
from app.dependencies.db import OrganizationRepository
from app.fulfilment.constants import (
    COMPLETED_TEMPLATE_TYPE,
    MPT_ORDER_STATUS_PROCESSING,
    ORDER_TYPE_PURCHASE,
    PROCESSING_TEMPLATE_TYPE,
    PURCHASE_EXISTING_TEMPLATE_NAME,
    PURCHASE_TEMPLATE_NAME,
    QUERYING_TEMPLATE_TYPE,
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
from app.fulfilment.parameters import check_order_parameters, get_parameter_updates
from app.fulfilment.subscriptions import get_subscription_by_line_and_item_id
from app.parameters import (
    PARAM_ADMIN_CONTACT,
    PARAM_CURRENCY,
    PARAM_IS_NEW_USER,
    PARAM_ORGANIZATION_NAME,
    get_due_date,
    get_fulfillment_parameter,
    get_ordering_parameter,
    set_fulfillment_parameter,
    set_is_new_user,
)

logger = logging.getLogger(__name__)


class ExceptionProcessResult(enum.StrEnum):
    COMPLETE = "Complete"
    RESCHEDULE = "Reschedule"
    CANCEL = "Cancel"
    SKIP = "Skip"


class OrderProcessor:
    def __init__(
        self,
        api_modifier_client: APIModifierClient,
        client: InstallationClient,
        ext_client: MPTClient,
        optscale_auth_client: OptscaleAuthClient,
        optscale_client: OptscaleClient,
        organization_repo: OrganizationRepository,
        settings: AppSettings,
        order: dict[str, Any],
    ):
        self.api_modifier_client = api_modifier_client
        self.client = client
        self.ext_client = ext_client
        self.optscale_auth_client = optscale_auth_client
        self.optscale_client = optscale_client
        self.organization_repo = organization_repo
        self.settings = settings
        self.order = order
        self.template_cache = {}

    def set_template(self, order: dict, template_id: str) -> dict:
        """Return a copy of the order with the provided template assigned."""
        if not template_id:
            raise ValueError("Template id is required")
        updated_order = copy.deepcopy(order)
        try:
            updated_order["template"]["id"] = template_id
            self.order = updated_order
            return self.order
        except KeyError:
            raise KeyError("Order is malformed")

    async def get_complete_template(self, is_new: bool) -> str | None | Any:
        if is_new:
            template_name = PURCHASE_TEMPLATE_NAME
        else:
            template_name = PURCHASE_EXISTING_TEMPLATE_NAME

        template_id = await self.get_product_template_id(COMPLETED_TEMPLATE_TYPE, template_name)
        return template_id

    async def get_product_template_id(
        self, template_type: str, template_name: str | None
    ) -> str | None | Any:
        product_id = self.settings.mpt_product_id
        if not self.template_cache:
            logger.info("Initializing template cache for product %s", product_id)
            await self.fetch_product_templates(product_id)
            logger.info("Template cache initialized with %d entries", len(self.template_cache))
        logger.info("Fetching template %s", template_name)
        return self.template_cache.get(
            (template_type, template_name), self.template_cache[(template_type, None)]
        )

    async def fetch_product_templates(self, product_id: str) -> None:
        async for template in self.ext_client.get_templates_by_product_id(product_id=product_id):
            template_id = template["id"]
            template_type = template["type"]
            template_name = template["name"] if not template["default"] else None
            self.template_cache[(template_type, template_name)] = template_id
            logger.debug("Cached template %s (%s, %s)", template_id, template_type, template_name)

    async def set_processing_order_template(self, order: dict) -> dict:
        """Ensure the order uses the processing template expected for purchase flow."""
        template_id = await self.get_product_template_id(
            PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME
        )
        logger.info("Processing order template: %s", template_id)
        current_template_id = self.order.get("template", {}).get("id")
        if template_id != current_template_id:
            order = self.set_template(order=order, template_id=template_id)
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

        logger.info("%s: processing template is ok, continue", order["id"])
        return self.order

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

    async def validate_order(self):
        if self.order["status"] != MPT_ORDER_STATUS_PROCESSING:
            raise OrderNotValidError(f"Order {self.order['id']} is not in Processing status")

        is_valid = await self.validate_and_move_to_querying_if_needed()
        if not is_valid:
            raise OrderMovedToQuery(f"Order {self.order['id']} is not valid")

    async def apply_fulfillment_defaults(self) -> dict[str, Any]:
        updated_parameters = get_parameter_updates(self.order, self.settings)
        order = self.order
        if updated_parameters:
            for param_name, param_value in updated_parameters.items():
                order = set_fulfillment_parameter(
                    order=order,
                    parameter=param_name,
                    value=param_value,
                )
            order = await self.ext_client.update_order(
                order_id=order["id"], parameters=order["parameters"]
            )
            logger.info("%s: updating fulfillment parameters", order["id"])
        self.order = order
        return self.order

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
            optscale_org = organization_on_optscale.json()
            logger.info("Organization on OptScale created with id %s ", optscale_org["id"])
            await self.ext_client.update_agreement(
                agreement_id,
                externalIds={"vendor": organization.id},
            )
            await self.organization_repo.update(
                organization.id,
                {
                    "linked_organization_id": optscale_org["id"],
                },
            )
            logger.info(
                "%s: Updating organization %s with external id to %s ",
                self.order["id"],
                organization.id,
                optscale_org["id"],
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
            # await optscale_client.reset_password(email)
            is_new = True
            logger.info("Employee created with id %s for order %s", employee_id, self.order["id"])
        updated_order = set_is_new_user(self.order, is_new=is_new)
        self.order = await self.ext_client.update_order(
            self.order["id"],
            parameters=updated_order["parameters"],
        )
        logger.debug("Updated orders %s %s ", updated_order["parameters"], self.order["parameters"])
        return employee_id, email

    async def create_order_subscription(self, organization: Organization):
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

    async def process(self):
        raise NotImplementedError()

    async def handle_exception(self, exc, now):
        pass


class PurchaseOrderProcessor(OrderProcessor):
    async def send_reset_password(self, employee_email: str, is_new: bool):
        if is_new:
            try:
                await self.optscale_client.reset_password(employee_email)
                logger.info("Employee %s password reset sent", employee_email)

            except Exception:
                logger.exception("Failed to reset password")
        else:
            logger.info("No need to send reset password", employee_email)

    async def process(self):
        await self.validate_order()
        await self.apply_fulfillment_defaults()
        await self.set_processing_order_template(order=self.order)
        employee_id, employee_email = await self.create_employee()
        organization = await self.get_or_create_organization(employee_id)

        await self.create_order_subscription(organization)
        is_new_user_param = get_fulfillment_parameter(self.order, PARAM_IS_NEW_USER)
        is_new = is_new_user_param.get("value") == ["Yes"]
        template_id = await self.get_complete_template(is_new)

        await self.ext_client.complete_order(
            order_id=self.order["id"], payload={"template": {"id": template_id}}
        )

        await self.send_reset_password(employee_email, is_new)
        logger.info("Order %s has been completed", self.order["id"])
        return self.order  # return ORDER_COMPLETED

    async def handle_exception(self, exc: Exception, *, now: date):
        if isinstance(exc, UnsupportedOrderTypeError):
            # fail order
            await self.ext_client.fail_order(
                order_id=self.order["id"],
                payload=ERR_ORDER_TYPE_NOT_SUPPORTED.to_dict(order_type=exc.order_type),
            )
            return ExceptionProcessResult.COMPLETE
        if isinstance(exc, OrderMovedToQuery | OrderNotValidError):
            # no fail order
            return ExceptionProcessResult.SKIP

        due_date: date | None = get_due_date(self.order) if self.order else None
        if due_date is None:
            # fail order
            await self.ext_client.fail_order(
                order_id=self.order["id"],
                payload=ERR_ORDER_TYPE_NOT_SUPPORTED.to_dict(order_type=exc.order_type),
            )
            return ExceptionProcessResult.CANCEL, ERR_DUE_DATE_NOT_SET.to_dict()
        if now < due_date:
            # reschedule
            return ExceptionProcessResult.RESCHEDULE
        else:
            # fail order
            await self.ext_client.fail_order(
                order_id=self.order["id"],
                payload=ERR_ORDER_TYPE_NOT_SUPPORTED.to_dict(order_type=exc.order_type),
            )
            return ExceptionProcessResult.COMPLETE, ERR_DUE_DATE_NOT_SET.to_dict(
                payload=ERR_DUE_DATE_IS_REACHED.to_dict(due_date=due_date.strftime("%Y-%m-%d")),
            )


PROCESSOR_BY_TYPE: dict[str, type["OrderProcessor"]] = {
    ORDER_TYPE_PURCHASE: PurchaseOrderProcessor,
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
        settings: AppSettings,
    ):
        self.api_modifier_client = api_modifier_client
        self.client = client
        self.ext_client = ext_client
        self.optscale_auth_client = optscale_auth_client
        self.optscale_client = optscale_client
        self.organization_repo = organization_repo
        self.settings = settings

    async def get_order_type_processor(self, order_id: str) -> OrderProcessor:
        order = await self.client.get_order(order_id)
        order_type = order["type"]
        try:
            processor_cls = PROCESSOR_BY_TYPE[order_type]
            return processor_cls(
                api_modifier_client=self.api_modifier_client,
                client=self.client,
                ext_client=self.ext_client,
                optscale_auth_client=self.optscale_auth_client,
                optscale_client=self.optscale_client,
                organization_repo=self.organization_repo,
                order=order,
                settings=self.settings,
            )
        except KeyError as exc:
            raise UnsupportedOrderTypeError(order_type) from exc
