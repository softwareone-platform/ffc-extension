from typing import ClassVar

from app.events.processing import ProcessingResult, ProcessingStatus


class EventError(Exception):
    """
    Base for known, domain-level errors raised while processing an event.

    Every subclass declares the outcome it maps to, so a processor can raise instead of
    building a `ProcessingResult` by hand, and the task layer knows what to do with an
    error raised outside a processor (e.g. while resolving one).
    """

    status: ClassVar[ProcessingStatus] = ProcessingStatus.CANCEL
    severity: ClassVar[str] = "Error"

    def to_result(self) -> ProcessingResult:
        return ProcessingResult(status=self.status, severity=self.severity, message=str(self))
