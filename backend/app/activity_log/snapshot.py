"""JSON snapshots of ORM instances, built generically from the mapper."""

from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import attributes
from sqlalchemy.orm.attributes import instance_state

from app.activity_log.constants import MASK


def snapshot(obj: object) -> dict[str, Any]:
    """Return the loaded column values of `obj` as a JSON-safe dict.

    Only loaded attributes are read, so calling this inside a session event never
    triggers a lazy load. Columns declared with `info={"sensitive": True}` are masked.
    """
    state = instance_state(obj)
    data: dict[str, Any] = {}
    for attr in state.mapper.column_attrs:
        if attr.key not in state.dict:  # expired or never loaded: skip, never lazy-load
            continue
        column = attr.columns[0]
        value = state.dict[attr.key]
        data[attr.key] = MASK if column.info.get("sensitive") else jsonable_encoder(value)
    return data


def before_image(obj: object) -> dict[str, Any]:
    """Snapshot of `obj` as it was before the pending changes in the current flush.

    Starts from the current loaded values and overlays the previous value of every
    attribute with pending history. Must be called inside `before_flush`, while
    attribute history is still available.
    """
    state = instance_state(obj)
    data = snapshot(obj)
    for attr in state.mapper.column_attrs:
        history = attributes.get_history(obj, attr.key)
        if history.has_changes() and history.deleted:
            column = attr.columns[0]
            previous = history.deleted[0]
            data[attr.key] = MASK if column.info.get("sensitive") else jsonable_encoder(previous)
    return data
