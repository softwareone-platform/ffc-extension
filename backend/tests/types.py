from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any, Protocol, TypeVar

from app.db.models import Base
from app.events.orders.processing import OrderEventHandler, OrderProcessor
from app.schemas.core import Event

ModelT = TypeVar("ModelT", bound=Base)
ModelFactory = Callable[..., Awaitable[ModelT]]
EventFactory = Callable[..., Event]
OrderFactory = Callable[..., dict[str, Any]]
MPTSubscriptionFactory = Callable[..., dict[str, Any]]


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
HandlerBuilder = Callable[[dict[str, Any]], OrderEventHandler]
TemplatesMocker = Callable[..., None]
SubscriptionMocker = Callable[..., None]
OptscaleOrganizationMocker: Callable[..., None]
