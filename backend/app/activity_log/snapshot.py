from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm.attributes import instance_state

from app.activity_log.constants import MASK


def snapshot(obj: object) -> dict[str, Any]:
    """Return the loaded column values of `obj` as a JSON-safe dict."""
    state = instance_state(obj)
    data: dict[str, Any] = {}
    for attr in state.mapper.column_attrs:
        if attr.key not in state.dict:
            continue
        column = attr.columns[0]
        value = state.dict[attr.key]
        data[attr.key] = MASK if column.info.get("sensitive") else jsonable_encoder(value)
    return data
