from datetime import datetime
from typing import Annotated, Any

from pydantic import Field

from app.schemas.core import ActorReference, BaseSchema, IdSchema


class ChangeRecordRead(BaseSchema):
    object_type: Annotated[str, Field(max_length=100, examples=["organizations"])]
    object_id: Annotated[str, Field(max_length=64, examples=["FORG-1234-5678"])]
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None


class ActivityLogRead(IdSchema):
    timestamp: datetime
    actor: ActorReference
    action: Annotated[str, Field(max_length=100, examples=["organization.terminated"])]
    message: Annotated[str, Field(examples=["entitlements terminated"])]


class ActivityLogDetailRead(ActivityLogRead):
    changes: list[ChangeRecordRead] = Field(default_factory=list)
