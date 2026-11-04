"""Transparent activity log: session events plus a declarative registry.

See docs/activity-log-recorder-alternatives.md, Part 3.
"""

from app.activity_log.context import activity_actor
from app.activity_log.external import instrument
from app.activity_log.listeners import register_listeners
from app.activity_log.recorder import record_activity

__all__ = ["activity_actor", "instrument", "record_activity", "register_listeners"]
