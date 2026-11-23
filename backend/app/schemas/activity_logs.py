from datetime import datetime
from typing import Annotated, Any

from pydantic import Field

from app.enums import ActivityStatus
from app.schemas.core import ActorReference, BaseSchema, IdSchema


class ChangeRecordRead(BaseSchema):
    object_type: Annotated[str, Field(max_length=100, examples=["organizations"])]
    object_id: Annotated[str, Field(max_length=64, examples=["FORG-1234-5678"])]
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    recorded_at: datetime


class ActivityNoteRead(BaseSchema):
    at: datetime
    actor_id: Annotated[str, Field(examples=["FAPP-0001"])]
    message: Annotated[str, Field(examples=["Waiting for the datasource to be created."])]


class ActivityLogRead(IdSchema):
    timestamp: datetime
    actor: ActorReference
    action: Annotated[str, Field(max_length=100, examples=["organization.terminated"])]
    message: Annotated[str, Field(examples=["entitlements terminated"])]
    status: ActivityStatus


class ActivityLogDetailRead(ActivityLogRead):
    operation_key: Annotated[
        str | None, Field(max_length=150, examples=["order:ORD-1234-5678-9012"])
    ] = None
    notes: list[ActivityNoteRead] = Field(default_factory=list)
    changes: list[ChangeRecordRead] = Field(default_factory=list)
