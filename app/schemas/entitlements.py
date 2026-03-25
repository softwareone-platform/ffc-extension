import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field

from app.enums import DatasourceType, EntitlementStatus
from app.schemas.accounts import AccountReference
from app.schemas.core import (
    AuditEventsSchema,
    AuditFieldSchema,
    BaseSchema,
    IdSchema,
)
from app.schemas.organizations import OrganizationReference


class EntitlementBase(BaseSchema):
    name: Annotated[str, Field(min_length=1, max_length=255, examples=["Microsoft CSP"])]
    affiliate_external_id: Annotated[
        str, Field(min_length=1, max_length=255, examples=["SUB-9876-5534-9172"])
    ]
    datasource_id: Annotated[
        str, Field(min_length=1, max_length=255, examples=["1098a2fa-07c0-4f40-96c7-3bf32a213e0e"])
    ]
    redeem_at: datetime.datetime | None = None


class EntitlementCreate(EntitlementBase):
    owner: IdSchema | None = None


class EntitlementUpdate(BaseSchema):
    name: Annotated[str | None, Field(min_length=1, max_length=255, examples=["Microsoft CSP"])] = (
        None
    )
    affiliate_external_id: Annotated[
        str | None, Field(min_length=1, max_length=255, examples=["SUB-9876-5534-9172"])
    ] = None
    datasource_id: Annotated[
        str | None,
        Field(min_length=1, max_length=255, examples=["1098a2fa-07c0-4f40-96c7-3bf32a213e0e"]),
    ] = None


class EntitlementReedemEventSchema(AuditFieldSchema):
    at: datetime.datetime
    by: OrganizationReference  # type: ignore


class EntitlementsEventsSchema(AuditEventsSchema):
    redeemed: EntitlementReedemEventSchema | None = None
    terminated: AuditFieldSchema | None = None


class EntitlementRead(IdSchema, EntitlementBase):
    linked_datasource_id: Annotated[
        str | None, Field(max_length=255, examples=["ee7ebfaf-a222-4209-aecc-67861694a488"])
    ] = None
    linked_datasource_name: Annotated[
        str | None, Field(max_length=255, examples=["Azure Dev Subscription"])
    ] = None
    linked_datasource_type: DatasourceType | None = None
    owner: AccountReference
    status: EntitlementStatus
    events: EntitlementsEventsSchema


class DatasourceInfo(BaseSchema):
    id: UUID
    name: str
    type: DatasourceType


class EntitlementRedeemInput(BaseSchema):
    organization: IdSchema
    datasource: DatasourceInfo
