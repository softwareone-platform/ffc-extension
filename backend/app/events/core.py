import logging
import traceback
from abc import ABC, abstractmethod
from typing import ClassVar

from app.api_clients.mpt import MPTClient
from app.events.exceptions import EventError
from app.events.processing import ProcessingResult, ProcessingStatus
from app.schemas.core import ExtensionContext

logger = logging.getLogger(__name__)


class EventProcessor(ABC):
    """
    Process the marketplace object event points at and report the outcome.

    Subclasses fill in the three steps of `process`:
      * `validate` rejects what must not be processed, by raising an `EventError`;
      * `handle` does the domain work and returns the terminal result;
      * `recover` decides what to do with an unexpected failure (retry, by default).
    """

    object_type: ClassVar[str]

    @property
    @abstractmethod
    def object_id(self) -> str:
        """Id of the object being processed, used for logging and messages."""

        raise NotImplementedError()

    async def validate(self) -> None:
        return None

    @abstractmethod
    async def handle(self) -> ProcessingResult:
        raise NotImplementedError()

    async def recover(self, exc: Exception) -> ProcessingResult:
        """Turn an unexpected failure into a result: retry the event by default."""

        return ProcessingResult(
            status=ProcessingStatus.RESCHEDULE,
            severity="Warning",
            message=f"An error occurred while processing the {self.object_type} "
            f"{self.object_id}: {traceback.format_exc()}",
        )

    async def on_event_error(self, exc: EventError) -> ProcessingResult:
        """
        Decide what a known domain error means for this processor.

        By default, the error's own declaration wins; a processor whose retry policy
        should have the last word (orders and their due date) overrides this.
        """

        return exc.to_result()

    async def process(self) -> ProcessingResult:
        try:
            await self.validate()
            return await self.handle()
        except EventError as exc:
            logger.info("%s: %s", self.object_id, exc)
            return await self.on_event_error(exc)
        except Exception as exc:
            logger.exception("%s: %s processing failed.", self.object_id, self.object_type)
            return await self.recover(exc)


class EventHandler(ABC):
    """
    Subclasses own the clients and repositories their domain needs, and must expose
    `ext_client`: the marketplace client the task layer logs and transitions tasks through.
    """

    ext_client: MPTClient

    async def claim_task(self, ext_ctx: ExtensionContext, task_id: str, object_id: str) -> bool:
        """
        Start the task and tell whether this event should be processed at all.

        The default claim only starts the task. Override to add an event type specific
        guard, the way orders check that this instance is the fulfilment owner.
        """

        logger.info("Changing task %s status to Processing", task_id)
        await self.ext_client.start_task(task_id, ext_ctx.instance_id)
        return True

    @abstractmethod
    async def get_processor(self, object_id: str) -> EventProcessor:
        """Fetch the object the event points at and return the processor that handles it."""

        raise NotImplementedError()
