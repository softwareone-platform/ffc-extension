from __future__ import annotations

import datetime
from typing import Annotated

from pydantic import EmailStr, Field

from app.enums import AccountUserStatus, UserStatus
from app.schemas.accounts import AccountReference
from app.schemas.core import BaseSchema, CommonEventsSchema, IdSchema, PasswordInputSchema


class UserBase(BaseSchema):
    name: Annotated[str, Field(max_length=255, examples=["Lady Gaga"])]


class UserCreate(UserBase):
    email: Annotated[EmailStr, Field(max_length=255, examples=["lady.gaga@bennett.tony"])]


class UserReference(IdSchema, UserCreate):
    pass


class UserAcceptInvitation(PasswordInputSchema):
    invitation_token: str


class UserResetPassword(PasswordInputSchema):
    pwd_reset_token: str


class UserUpdate(BaseSchema):
    name: str


class AccountUserBase(BaseSchema):
    status: AccountUserStatus


class AccountUserCreate(BaseSchema):
    account: IdSchema | None = None
    name: Annotated[str, Field(max_length=255, examples=["Lady Gaga"])]
    email: Annotated[EmailStr, Field(max_length=255, examples=["lady.gaga@bennett.tony"])]


class AccountUserRead(IdSchema, CommonEventsSchema, AccountUserBase):
    account: AccountReference
    user: UserReference
    invitation_token: str | None
    invitation_token_expires_at: datetime.datetime | None
    joined_at: datetime.datetime | None = None


class AccountUserReference(IdSchema, AccountUserBase):
    created_at: datetime.datetime | None = None
    joined_at: datetime.datetime | None = None


class AccountUserReferenceWithUser(AccountUserReference):
    user: UserReference


class AccountUserReferenceWithAccount(AccountUserReference):
    account: AccountReference


class UserInvitationRead(IdSchema, CommonEventsSchema, UserCreate):
    account_user: AccountUserRead | None = None
    status: UserStatus


class UserRead(IdSchema, CommonEventsSchema, UserCreate):
    status: UserStatus
    last_login_at: datetime.datetime | None
    last_used_account: AccountReference | None
    account_user: AccountUserReferenceWithAccount | None
