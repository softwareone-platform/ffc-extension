from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Protocol, TypeVar

from app.db.models import Base

ModelT = TypeVar("ModelT", bound=Base)
ModelFactory = Callable[..., Awaitable[ModelT]]


class JWTTokenFactory(Protocol):
    def __call__(
        self,
        subject: str,
        secret: str,
        account_id: str | None = None,
        exp: datetime | None = None,
        iat: datetime | None = None,
        nbf: datetime | None = None,
    ) -> str: ...
