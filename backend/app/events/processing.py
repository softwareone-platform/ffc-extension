import enum
from dataclasses import dataclass


class ProcessingStatus(enum.StrEnum):
    COMPLETE = "Complete"
    RESCHEDULE = "Reschedule"
    CANCEL = "Cancel"
    SKIP = "Skip"


@dataclass
class ProcessingResult:
    status: ProcessingStatus
    severity: str | None = None
    message: str | None = None
