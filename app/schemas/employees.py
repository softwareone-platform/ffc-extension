import datetime
import uuid
from typing import Annotated

from pydantic import ConfigDict, Field

from app.schemas.core import BaseSchema


class EmployeeBase(BaseSchema):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
    email: Annotated[
        str, Field(min_length=1, max_length=255, examples=["harry.potter@gryffindor.edu"])
    ]
    display_name: Annotated[
        str, Field(min_length=1, max_length=255, examples=["Harry James Potter"])
    ]
    created_at: datetime.datetime | None = None
    last_login: datetime.datetime | None = None
    roles_count: int | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeRead(EmployeeBase):
    id: uuid.UUID
