from typing import ClassVar

import httpx

from app.events.processing import ProcessingResult, ProcessingStatus


class ProcessError(Exception):
    """
    Base for known, domain-level errors raised while processing an event.

    Every subclass declares the outcome it maps to, so a processor can raise instead of
    building a `ProcessingResult` by hand, and the task layer knows what to do with an
    error raised outside a processor (e.g. while resolving one).
    """

    status: ClassVar[ProcessingStatus]
    severity: ClassVar[str]

    def to_result(self) -> ProcessingResult:
        return ProcessingResult(status=self.status, severity=self.severity, message=str(self))


class EventError(ProcessError):
    """Domain-level error raised by processors and by _get_processor
    (unsupported order type, subscription not found, order moved to query)
    Cancels the task unless the subclass overrides the behavior"""

    status = ProcessingStatus.CANCEL
    severity = "Error"


class HandlerError(ProcessError):
    """Lifecycle-level errors raised by claim_task and get_processor.
    Reschedules the task unless the subclass overrides the behavior"""

    status: ClassVar[ProcessingStatus] = ProcessingStatus.RESCHEDULE
    severity: ClassVar[str] = "Error"


class HandlerHTTPError(HandlerError):
    """An MPT call returned a non-2xx status code."""

    def __init__(self, fnc: str, object_id: str, exc: httpx.HTTPStatusError) -> None:
        request = exc.request
        response = exc.response
        super().__init__(
            f"{fnc} failed for {object_id} "
            f"{request.method} {request.url.path} {response.status_code} {response.reason_phrase}"
        )


class TaskNotOwnedError(HandlerError):
    """The task belongs to another account: close it, nothing to process"""

    status = ProcessingStatus.COMPLETE
    severity = "Info"
    send_notification = False
