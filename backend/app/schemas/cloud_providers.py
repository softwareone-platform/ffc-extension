from typing import Annotated

from pydantic import Field, StringConstraints

from app.schemas.core import BaseSchema, IdSchema


class CloudProviderBase(BaseSchema):
    name: Annotated[
        str,
        Field(min_length=1, max_length=255, examples=["Microsoft Azure"]),
        StringConstraints(strip_whitespace=True),
    ]
    icon: Annotated[
        str,
        Field(
            min_length=1,
            max_length=64,
            examples=["microsoft"],
        ),
    ]
    datasource_id_format: Annotated[
        str,
        Field(
            min_length=1,
            max_length=512,
        ),
    ]


class CloudProviderRead(IdSchema, CloudProviderBase):
    pass
