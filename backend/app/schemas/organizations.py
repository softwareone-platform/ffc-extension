import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Annotated, Any

import pycountry
from pydantic import ConfigDict, Field, computed_field, field_validator, model_validator

from app.enums import (
    AwsAccountType,
    AwsAuthenticationType,
    AwsExportType,
    DatasourceImportStatus,
    DatasourceType,
    OrganizationStatus,
    TerminationReason,
)
from app.schemas.core import (
    AuditEventsSchema,
    AuditFieldSchema,
    BaseSchema,
    CommonEventsSchema,
    IdSchema,
)
from app.utils import get_organization_deletable_at

# Optscale reports "never imported" as 0, which pydantic coerces to the epoch.
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)

EXCLUDED_CURRENCIES = [
    "XAU",  # gold
    "XAG",  # silver
    "XPD",  # palladium
    "XPT",  # platinum
    "XBA",  # European Composite Unit (EURCO) (bond market unit)
    "XBB",  # European Monetary Unit (E.M.U.-6) (bond market unit)
    "XBC",  # European Unit of Account 9 (E.U.A.-9) (bond market unit)
    "XBD",  # European Unit of Account 17 (E.U.A.-17) (bond market unit)
    "XDR",  # Special drawing rights (International Monetary Fund)
    "XSU",  # Unified System for Regional Compensation (SUCRE)
    "XTS",  # reserved for testign
    "XXX",  # No currency
]


class OrganizationExpensesInfo(BaseSchema):
    limit: Annotated[Decimal, Field(examples=["10000.00"], default=Decimal(0))]
    expenses_this_month: Annotated[Decimal, Field(examples=["2111.49"], default=Decimal(0))]
    expenses_this_month_forecast: Annotated[
        Decimal, Field(examples=["5001.12"], default=Decimal(0))
    ]
    possible_monthly_saving: Annotated[Decimal, Field(examples=["4.66"], default=Decimal(0))]


class OrganizationBase(BaseSchema):
    name: Annotated[str, Field(min_length=1, max_length=255, examples=["Red Hat"])]
    currency: Annotated[str, Field(min_length=3, max_length=3, examples=["USD"])]
    billing_currency: Annotated[str, Field(min_length=3, max_length=3, examples=["EUR"])]
    operations_external_id: Annotated[
        str, Field(min_length=1, max_length=255, examples=["AGR-9876-5534-9172"])
    ]

    @field_validator("currency", "billing_currency")
    @classmethod
    def validate_currency(cls, currency: str) -> str:
        if currency and (
            currency in EXCLUDED_CURRENCIES or not pycountry.currencies.get(alpha_3=currency)
        ):
            raise ValueError(f"Invalid iso4217 currency code: {currency}.")
        return currency


class OrganizationCreate(OrganizationBase):
    user_id: Annotated[
        str, Field(min_length=1, max_length=255, examples=["ee7ebfaf-a222-4209-aecc-67861694a488"])
    ]


class OrganizationEventsSchema(AuditEventsSchema):
    terminated: AuditFieldSchema | None = None


class TerminationFeedbackRead(IdSchema):
    reason: Annotated[
        TerminationReason,
        Field(
            examples=[TerminationReason.SWITCHING_TOOL],
            description="Reason given by the client for terminating the agreement.",
        ),
    ]
    comments: Annotated[
        str | None,
        Field(
            examples=["We are consolidating our FinOps tooling."],
            description="Additional comments; always provided when the reason is `other`.",
        ),
    ] = None


class ClientAccountReference(IdSchema):
    name: Annotated[str, Field(max_length=255, examples=["Red Hat Inc."])]
    external_id: Annotated[str, Field(max_length=255, examples=["ACC-1234-5678"])]
    icon: Annotated[
        str | None, Field(max_length=255, examples=["/v1/accounts/ACC-1234-5678/icon"])
    ] = None


class OrganizationRead(IdSchema, OrganizationBase):
    linked_organization_id: Annotated[
        str | None, Field(max_length=255, examples=["ee7ebfaf-a222-4209-aecc-67861694a488"])
    ] = None
    status: OrganizationStatus
    client: Annotated[
        ClientAccountReference | None,
        Field(
            validation_alias="client_account",
            description="The client account the organization belongs to, if any.",
        ),
    ] = None
    events: OrganizationEventsSchema
    expenses_info: OrganizationExpensesInfo | None = None
    termination_feedback: Annotated[
        TerminationFeedbackRead | None,
        Field(
            description=(
                "Feedback given by the client when terminating the agreement. "
                "Omitted if no feedback was collected."
            ),
        ),
    ] = None

    @computed_field(  # type: ignore[prop-decorator]
        examples=["2026-09-01T00:00:00Z"],
        description=(
            "The moment from which a terminated organization can be deleted, "
            "null if the organization has not been terminated."
        ),
    )
    @property
    def deletable_at(self) -> datetime | None:
        if self.events.terminated is None:
            return None

        return get_organization_deletable_at(self.events.terminated.at)


class OrganizationUpdate(BaseSchema):
    name: Annotated[str | None, Field(min_length=1, max_length=255, examples=["red hat"])] = None
    operations_external_id: Annotated[
        str | None, Field(min_length=1, max_length=255, examples=["AGR-9876-5534-9172"])
    ] = None


class OrganizationReference(IdSchema):
    name: str
    operations_external_id: str


class DatasourceBase(BaseSchema):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    id: uuid.UUID
    name: str
    type: DatasourceType
    datasource_id: str | None = Field(default=None, validation_alias="account_id")


class DatasourceRead(DatasourceBase):
    parent: DatasourceBase | None = None
    parent_id: uuid.UUID | None = None
    # Not every upstream payload carries the import timestamps: default them to the epoch so
    # that a datasource that has never been imported is reported the same way Optscale does.
    last_import_at: datetime = EPOCH
    last_import_modified_at: datetime = EPOCH
    last_import_attempt_at: datetime = EPOCH
    last_import_attempt_error: str | None = None
    resources_charged_this_month: int = Field(validation_alias="resources")
    expenses_so_far_this_month: float = Field(validation_alias="cost")
    expenses_forecast_this_month: float = Field(validation_alias="forecast")


class DatasourceUpstreamSchema(BaseSchema):
    # Mirrors an FFC API payload: ignore unknown fields so upstream additions don't break us.
    model_config = ConfigDict(extra="ignore")


class AzureSubscriptionDetails(DatasourceUpstreamSchema):
    connected_at: datetime | None = None
    parent: DatasourceBase | None = None
    subscription_id: Annotated[
        str | None, Field(examples=["5f3a1c2e-9d4b-4e8a-b1f7-2c6d8e0a3b5f"])
    ] = None
    tenant_id: Annotated[str | None, Field(examples=["8b1d7e4a-3c2f-4a9b-8e6d-1f0a5c7b9d2e"])] = (
        None
    )
    client_id: Annotated[str | None, Field(examples=["c2a9f0b3-7e1d-4b6a-9c8f-3d5e2a1b0c4f"])] = (
        None
    )


class AzureTenantDetails(DatasourceUpstreamSchema):
    connected_at: datetime | None = None
    tenant_id: Annotated[str | None, Field(examples=["8b1d7e4a-3c2f-4a9b-8e6d-1f0a5c7b9d2e"])] = (
        None
    )
    client_id: Annotated[str | None, Field(examples=["c2a9f0b3-7e1d-4b6a-9c8f-3d5e2a1b0c4f"])] = (
        None
    )


class AwsDetails(DatasourceUpstreamSchema):
    """
    `assumed_role_name` is returned only for assumed role authentication,
    `access_key_id` only for access key authentication and the export fields
    only for management/standalone accounts.
    """

    connected_at: datetime | None = None
    account_id: Annotated[str | None, Field(examples=["203589795269"])] = None
    account_type: AwsAccountType
    authentication_type: AwsAuthenticationType
    assumed_role_name: Annotated[str | None, Field(examples=["FinOpsReadOnly"])] = None
    access_key_id: Annotated[str | None, Field(examples=["AKIAIOSFODNN7EXAMPLE"])] = None
    export_type: AwsExportType | None = None
    use_edp_discount: bool | None = None
    export_name: Annotated[str | None, Field(examples=["optscale-export"])] = None
    bucket_name: Annotated[str | None, Field(examples=["optscale-bucket"])] = None
    bucket_prefix: Annotated[str | None, Field(examples=["reports"])] = None
    region_name: Annotated[str | None, Field(examples=["eu-central-1"])] = None
    included_regions: Annotated[list[str] | None, Field(examples=[["eu-central-1"]])] = None
    excluded_regions: Annotated[list[str] | None, Field(examples=[["us-east-1"]])] = None


class GcpDetails(DatasourceUpstreamSchema):
    connected_at: datetime | None = None
    project_id: Annotated[str | None, Field(examples=["my-gcp-project"])] = None
    billing_dataset_name: Annotated[str | None, Field(examples=["billing_export"])] = None
    billing_table_name: Annotated[
        str | None, Field(examples=["gcp_billing_export_v1_0123AB_456CDE_789EFG"])
    ] = None
    billing_project_id: Annotated[str | None, Field(examples=["my-billing-project"])] = None


DatasourceDetails = AzureSubscriptionDetails | AzureTenantDetails | AwsDetails | GcpDetails

DATASOURCE_DETAILS_SCHEMAS: dict[DatasourceType, type[DatasourceUpstreamSchema]] = {
    DatasourceType.AZURE_CNR: AzureSubscriptionDetails,
    DatasourceType.AZURE_TENANT: AzureTenantDetails,
    DatasourceType.AWS_CNR: AwsDetails,
    DatasourceType.GCP_CNR: GcpDetails,
}


class DatasourceBillingInfo(DatasourceUpstreamSchema):
    last_report_processed_at: datetime | None = None
    last_attempt_at: datetime | None = None
    last_report_updated_at: datetime | None = None
    status: DatasourceImportStatus
    error: Annotated[str | None, Field(examples=["Bucket not found"])] = None


class DatasourceMetricsInfo(DatasourceUpstreamSchema):
    last_retrieval_at: datetime | None = None
    last_attempt_at: datetime | None = None
    status: DatasourceImportStatus
    error: str | None = None


class DatasourceDiscoveryItem(DatasourceUpstreamSchema):
    resource_type: Annotated[str | None, Field(examples=["instance"])] = None
    enabled: bool | None = None
    last_discovery_at: datetime | None = None
    last_error_at: datetime | None = None
    status: DatasourceImportStatus
    error: str | None = None


class DatasourceDetailRead(DatasourceRead):
    details: DatasourceDetails | None = None
    billing: DatasourceBillingInfo
    metrics: DatasourceMetricsInfo
    discovery: list[DatasourceDiscoveryItem] = []

    @model_validator(mode="before")
    @classmethod
    def validate_details(cls, data: Any) -> Any:
        # The upstream details carry no type tag and their shapes overlap (e.g. an Azure tenant
        # payload is also a valid Azure subscription one): pick the schema from the datasource type.
        if not isinstance(data, dict) or not isinstance(data.get("details"), dict):
            return data

        schema = DATASOURCE_DETAILS_SCHEMAS.get(DatasourceType(data.get("type")))
        return {**data, "details": schema.model_validate(data["details"]) if schema else None}


class DatasourceForceReimport(BaseSchema):
    last_import_at: Annotated[
        date | None,
        Field(
            default=None,
            examples=["2026-09-01"],
            description=(
                "Date, in ISO format, to set as the datasource's last import timestamp before "
                "scheduling the reimport. When omitted it defaults to the epoch (0), which "
                "reimports all the available expenses."
            ),
        ),
    ] = None

    @property
    def last_import_at_timestamp(self) -> int:
        """`last_import_at` as seconds since the epoch at UTC midnight, or 0 when not provided."""
        if self.last_import_at is None:
            return 0

        return int(datetime.combine(self.last_import_at, time.min, tzinfo=UTC).timestamp())


class AdditionalAdminRequestBase(BaseSchema):
    email: str
    notes: Annotated[str, Field(min_length=1, max_length=100, examples=["What a wonderful world"])]
    display_name: Annotated[str, Field(min_length=1, max_length=50, examples=["Perter Parker"])]


class AdditionalAdminRequestCreate(AdditionalAdminRequestBase):
    pass


class AdditionalAdminRequestRead(IdSchema, CommonEventsSchema, AdditionalAdminRequestBase):
    pass
