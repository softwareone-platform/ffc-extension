import pytest
from pydantic import BaseModel, ValidationError

from app.db.models import Account
from app.schemas.core import (
    AuditFieldSchema,
    PasswordInputSchema,
    extract_events,
    resolve_field_type,
)


class _UnsupportedEventsSchema(BaseModel):
    created: int


def test_resolve_field_type_unwraps_optional() -> None:
    """`resolve_field_type` returns the single non-None member of an optional union."""
    assert resolve_field_type(AuditFieldSchema | None) is AuditFieldSchema


def test_resolve_field_type_returns_plain_type() -> None:
    """`resolve_field_type` returns a non-union annotation unchanged."""
    assert resolve_field_type(AuditFieldSchema) is AuditFieldSchema


def test_resolve_field_type_rejects_multi_member_union() -> None:
    """`resolve_field_type` raises `TypeError` for a union with multiple non-None members."""
    with pytest.raises(TypeError, match="Unsupported union type"):
        resolve_field_type(int | str)


def test_extract_events_rejects_non_audit_field_schema() -> None:
    """`extract_events` raises `TypeError` when a field does not resolve to `AuditFieldSchema`."""
    with pytest.raises(TypeError, match="Unsupported schema type"):
        extract_events(Account(), _UnsupportedEventsSchema)


def test_password_input_schema_accepts_valid_password() -> None:
    """`PasswordInputSchema` accepts a password meeting every complexity rule."""
    schema = PasswordInputSchema(password="PKH7aqr_gwh5fgm!xdk")
    assert schema.password is not None
    assert schema.password.get_secret_value() == "PKH7aqr_gwh5fgm!xdk"


def test_password_input_schema_allows_none() -> None:
    """`PasswordInputSchema` allows an omitted password, leaving it None."""
    assert PasswordInputSchema().password is None  # type: ignore[call-arg]


@pytest.mark.parametrize(
    ("password", "message"),
    [
        ("Aa1!aaa", "at least 8 characters"),
        ("aaaaaaa1!", "one uppercase letter"),
        ("AAAAAAA1!", "one lowercase letter"),
        ("Aaaaaaaa!", "one number"),
        ("Aaaaaaa1", "one special character"),
    ],
)
def test_password_input_schema_rejects_weak_password(password: str, message: str) -> None:
    """`PasswordInputSchema` raises a validation error naming the unmet complexity rule."""
    with pytest.raises(ValidationError, match=message):
        PasswordInputSchema(password=password)
