import logging
from abc import ABC, abstractmethod
from functools import cached_property
from types import TracebackType
from typing import ClassVar, Self

import httpx

from app.conf import Settings

logger = logging.getLogger(__name__)


class APIClientError(Exception):
    client_name: ClassVar[str]

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.client_name = cls.__module__.split(".")[-1]

    def __init__(self, message: str):
        self.message = message

        super().__init__(f"{self.client_name} API client error: {message}")


class BaseAPIClient(ABC):
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    @abstractmethod
    def base_url(self):
        raise NotImplementedError("base_url property must be implemented in subclasses")

    @property
    @abstractmethod
    def auth(self):
        raise NotImplementedError("base_url property must be implemented in subclasses")

    @cached_property
    def httpx_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            auth=self.auth,
            timeout=httpx.Timeout(
                connect=0.25,
                read=self.settings.optscale_read_timeout,
                write=2.0,
                pool=5.0,
            ),
        )

    async def __aenter__(self) -> Self:
        await self.httpx_client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        return await self.httpx_client.__aexit__(exc_type, exc_val, exc_tb)
