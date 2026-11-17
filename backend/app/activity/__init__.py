"""Activity log: record who did what and what changed.

See `docs/proposals/activity-log-recorder.md` for the design.
"""

from app.activity.constants import APP_ACTOR_ID, MASK
from app.activity.recorder import (
    CAPTURE_OPTION,
    ActivityRecorder,
    ActivityRecorderError,
    activity_recorder,
)
from app.activity.snapshot import snapshot

__all__ = [
    "APP_ACTOR_ID",
    "CAPTURE_OPTION",
    "MASK",
    "ActivityRecorder",
    "ActivityRecorderError",
    "activity_recorder",
    "snapshot",
]
