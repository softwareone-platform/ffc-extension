from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any, Protocol, TypeVar

from app.db.models import Base
from app.fulfilment.processing import OrderProcessor, OrderProcessorFactory

ModelT = TypeVar("ModelT", bound=Base)
ModelFactory = Callable[..., Awaitable[ModelT]]
OrderFactory = Callable[..., dict[str, Any]]


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


ProcessorBuilder = Callable[[dict[str, Any]], OrderProcessor]
FactoryBuilder = Callable[[dict[str, Any]], OrderProcessorFactory]
TemplatesMocker = Callable[..., None]
