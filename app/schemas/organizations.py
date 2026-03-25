import uuid
from decimal import Decimal
from typing import Annotated

import pycountry
from pydantic import Field, field_validator

from app.enums import DatasourceType, OrganizationStatus
from app.schemas.core import BaseSchema, CommonEventsSchema, IdSchema

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
    limit: Annotated[Decimal, Field(max_length=255, examples=["10000.00"], default=Decimal(0))]
    expenses_last_month: Annotated[
        Decimal, Field(max_length=255, examples=["4321.26"], default=Decimal(0))
    ]
    expenses_this_month: Annotated[
        Decimal, Field(max_length=255, examples=["2111.49"], default=Decimal(0))
    ]
    expenses_this_month_forecast: Annotated[
        Decimal, Field(max_length=255, examples=["5001.12"], default=Decimal(0))
    ]
    possible_monthly_saving: Annotated[
        Decimal, Field(max_length=255, examples=["4.66"], default=Decimal(0))
    ]


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


class OrganizationRead(IdSchema, CommonEventsSchema, OrganizationBase):
    linked_organization_id: Annotated[
        str | None, Field(max_length=255, examples=["ee7ebfaf-a222-4209-aecc-67861694a488"])
    ] = None
    status: OrganizationStatus
    expenses_info: OrganizationExpensesInfo | None = None


class OrganizationUpdate(BaseSchema):
    name: Annotated[str | None, Field(min_length=1, max_length=255, examples=["red hat"])] = None
    operations_external_id: Annotated[
        str | None, Field(min_length=1, max_length=255, examples=["AGR-9876-5534-9172"])
    ] = None


class OrganizationReference(IdSchema):
    name: str
    operations_external_id: str


class DatasourceRead(BaseSchema):
    id: uuid.UUID
    name: str
    type: DatasourceType
    parent_id: uuid.UUID | None
    resources_charged_this_month: int
    expenses_so_far_this_month: float
    expenses_forecast_this_month: float
    datasource_id: str


class AdditionalAdminRequestBase(BaseSchema):
    email: str
    notes: Annotated[str, Field(min_length=1, max_length=100, examples=["What a wonderful world"])]
    display_name: Annotated[str, Field(min_length=1, max_length=50, examples=["Perter Parker"])]


class AdditionalAdminRequestCreate(AdditionalAdminRequestBase):
    pass


class AdditionalAdminRequestRead(IdSchema, CommonEventsSchema, AdditionalAdminRequestBase):
    pass
