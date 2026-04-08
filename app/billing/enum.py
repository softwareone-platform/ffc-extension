import enum
from enum import Enum


class JournalStatus(enum.StrEnum):
    DRAFT = "Draft"
    VALIDATED = "Validated"
    REVIEW = "Review"
    GENERATING = "Generating"
    GENERATED = "Generated"
    ACCEPTED = "Accepted"
    COMPLETED = "Completed"
    DELETED = "Deleted"
    TERMINATED = "Terminated"
    ACTIVE = "Active"


class ProcessResult(Enum):
    JOURNAL_SKIPPED = "journal_skipped"
    JOURNAL_GENERATED = "journal_generated"
    ERROR = "error"


class NotificationLevel(Enum):
    SUCCESS = "success"
    IN_PROGRESS = "in_progress"
    ERROR = "error"
