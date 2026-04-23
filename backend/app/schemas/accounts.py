from typing import Annotated

from pydantic import Field, computed_field

from app.enums import AccountStatus, AccountType
from app.schemas.core import BaseSchema, CommonEventsSchema, IdSchema


class EntitlementStats(BaseSchema):
    new: Annotated[int, Field(examples=["5"], default=0)]
    redeemed: Annotated[int, Field(examples=["4"], default=0)]
    terminated: Annotated[int, Field(examples=["12"], default=0)]


class AccountStats(BaseSchema):
    entitlements: EntitlementStats


class AccountBase(BaseSchema):
    name: Annotated[
        str,
        Field(
            min_length=1,
            max_length=255,
            examples=["Microsoft"],
            description="The name of the account",
        ),
    ]
    external_id: Annotated[
        str,
        Field(
            min_length=1,
            max_length=255,
            examples=["ACC-9044-8753"],
            description="An external identifier for the account",
        ),
    ]


class AccountCreate(AccountBase):
    type: AccountType


class AccountUpdate(BaseSchema):
    name: Annotated[str | None, Field(min_length=1, max_length=255, examples=["Microsoft"])] = None
    external_id: Annotated[
        str | None, Field(min_length=1, max_length=255, examples=["ACC-9044-8753"])
    ] = None


class AccountReference(IdSchema):
    name: Annotated[str, Field(max_length=255, examples=["Microsoft"])]
    type: AccountType


# Importing here to avoid circular imports
from app.schemas.users import AccountUserReferenceWithUser  # noqa: E402


class AccountRead(IdSchema, CommonEventsSchema, AccountBase):
    new_entitlements_count: int = Field(default=0, exclude=True)
    active_entitlements_count: int = Field(default=0, exclude=True)
    terminated_entitlements_count: int = Field(default=0, exclude=True)
    account_user: AccountUserReferenceWithUser | None
    status: AccountStatus
    type: AccountType

    @computed_field  # type: ignore[misc]
    @property
    def stats(self) -> AccountStats:
        return AccountStats(
            entitlements=EntitlementStats(
                new=self.new_entitlements_count,
                redeemed=self.active_entitlements_count,
                terminated=self.terminated_entitlements_count,
            )
        )
