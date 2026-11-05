from collections.abc import Mapping
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Mapper
from sqlalchemy.orm.attributes import instance_state

from app.activity.constants import MASK


def encode_values(values: Mapping[str, Any]) -> dict[str, Any]:
    """Return `values` as a JSON-safe dict (enums become values, datetimes ISO strings)."""
    return {key: jsonable_encoder(value) for key, value in values.items()}


def mask_sensitive(mapper: Mapper, values: Mapping[str, Any]) -> dict[str, Any]:
    """Replace the value of every column declared with `info={"sensitive": True}`."""
    sensitive = {attr.key for attr in mapper.column_attrs if attr.columns[0].info.get("sensitive")}
    return {key: MASK if key in sensitive else value for key, value in values.items()}


def snapshot(obj: object) -> dict[str, Any]:
    """Return the loaded column values of `obj` as a JSON-safe dict, sensitive columns masked."""
    state = instance_state(obj)
    loaded = {
        attr.key: state.dict[attr.key]
        for attr in state.mapper.column_attrs
        if attr.key in state.dict
    }
    return mask_sensitive(state.mapper, encode_values(loaded))
