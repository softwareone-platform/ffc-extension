import uuid
from decimal import Decimal
from typing import Annotated

import pycountry
from pydantic import ConfigDict, Field, field_validator

from app.enums import DatasourceType, OrganizationStatus
from app.schemas.core import (
    AuditEventsSchema,
    AuditFieldSchema,
    BaseSchema,
    CommonEventsSchema,
    IdSchema,
)

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


class OrganizationRead(IdSchema, OrganizationBase):
    linked_organization_id: Annotated[
        str | None, Field(max_length=255, examples=["ee7ebfaf-a222-4209-aecc-67861694a488"])
    ] = None
    status: OrganizationStatus
    events: OrganizationEventsSchema
    expenses_info: OrganizationExpensesInfo | None = None


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
    resources_charged_this_month: int = Field(validation_alias="resources")
    expenses_so_far_this_month: float = Field(validation_alias="cost")
    expenses_forecast_this_month: float = Field(validation_alias="forecast")


class AdditionalAdminRequestBase(BaseSchema):
    email: str
    notes: Annotated[str, Field(min_length=1, max_length=100, examples=["What a wonderful world"])]
    display_name: Annotated[str, Field(min_length=1, max_length=50, examples=["Perter Parker"])]


class AdditionalAdminRequestCreate(AdditionalAdminRequestBase):
    pass


class AdditionalAdminRequestRead(IdSchema, CommonEventsSchema, AdditionalAdminRequestBase):
    pass
