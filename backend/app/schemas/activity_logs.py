from datetime import datetime
from typing import Annotated, Any

from pydantic import Field, model_validator

from app.db.models import ActivityNote
from app.enums import ActivityStatus
from app.schemas.core import AuditFieldSchema, BaseSchema, IdSchema, convert_model_to_schema


class RecordedEventsSchema(BaseSchema):
    recorded: AuditFieldSchema


class ChangeRecordRead(BaseSchema):
    object_type: Annotated[str, Field(max_length=100, examples=["organizations"])]
    object_id: Annotated[str, Field(max_length=64, examples=["FORG-1234-5678"])]
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    recorded_at: datetime


class ActivityNoteRead(BaseSchema):
    events: RecordedEventsSchema
    message: Annotated[str, Field(examples=["Waiting for the datasource to be created."])]

    @model_validator(mode="before")
    @classmethod
    def build_events_from_model(cls, data: Any) -> Any:
        # Notes are serialized as a nested field of an activity log, so they do not go
        # through `convert_model_to_schema`, which is what builds `events` from a model.
        if isinstance(data, ActivityNote):
            return convert_model_to_schema(cls, data)
        return data


class ActivityLogRead(IdSchema):
    events: RecordedEventsSchema
    action: Annotated[str, Field(max_length=100, examples=["organization.terminated"])]
    message: Annotated[str, Field(examples=["entitlements terminated"])]
    status: ActivityStatus


class ActivityLogDetailRead(ActivityLogRead):
    operation_key: Annotated[
        str | None, Field(max_length=150, examples=["order:ORD-1234-5678-9012"])
    ] = None
    notes: list[ActivityNoteRead] = Field(default_factory=list)
    changes: list[ChangeRecordRead] = Field(default_factory=list)
