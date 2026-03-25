from typing import Annotated

from pydantic import EmailStr, Field, SecretStr

from app.schemas.accounts import AccountReference
from app.schemas.core import (
    BaseSchema,
    IdSchema,
)
from app.schemas.users import UserReference


class Login(BaseSchema):
    email: Annotated[EmailStr, Field(examples=["lady.gaga@bennett.tony"])]
    password: Annotated[SecretStr, Field(examples=["PKH7aqr_gwh5fgm!xdk"])]
    account: IdSchema | None = None


class LoginRead(BaseSchema):
    user: UserReference
    account: AccountReference
    access_token: Annotated[str, Field(examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey..."])]
    refresh_token: Annotated[str, Field(examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey..."])]


class RefreshAccessToken(BaseSchema):
    account: IdSchema
    refresh_token: Annotated[str, Field(examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ey..."])]
