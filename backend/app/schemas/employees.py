import datetime
import uuid
from typing import Annotated

from pydantic import ConfigDict, Field, computed_field

from app.schemas.core import BaseSchema


class EmployeeRole(BaseSchema):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    resource_type: Annotated[str | None, Field(examples=["organization", "pool"], default=None)]
    purpose: Annotated[str | None, Field(examples=["optscale_manager"], default=None)]


class EmployeeRead(BaseSchema):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    id: uuid.UUID
    email: Annotated[
        str, Field(min_length=1, max_length=255, examples=["harry.potter@gryffindor.edu"])
    ]
    display_name: Annotated[
        str, Field(min_length=1, max_length=255, examples=["Harry James Potter"])
    ]
    created_at: datetime.datetime | None = None
    last_login: datetime.datetime | None = None
    roles_count: int | None = None
    roles: list[EmployeeRole] = Field(default_factory=list, exclude=True)

    @computed_field  # type: ignore[misc]
    @property
    def is_admin(self) -> bool:
        return any(
            role.resource_type == "organization" and role.purpose == "optscale_manager"
            for role in self.roles
        )
