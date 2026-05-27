from __future__ import annotations

from app.schemas.accounts import AccountReference
from app.schemas.core import BaseSchema
from app.schemas.systems import SystemReference
from app.schemas.users import UserReference


class Me(BaseSchema):
    account: AccountReference
    system: SystemReference | None
    user: UserReference | None
