import base64
import secrets
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest
from fastapi import HTTPException, status
from pytest_mock import MockerFixture

from app.utils import (
    async_groupby,
    compute_daily_expenses,
    find_first,
    get_instance_external_id,
    get_jwt_token_claims,
    get_jwt_token_expires,
    get_meta,
    wrap_exc_in_http_response,
    wrap_http_error_in_502,
    wrap_http_not_found_in_400,
)


def _make_jwt(claims: dict) -> str:
    """Encode a signed JWT carrying the given claims (helper for token tests)."""
    return jwt.encode(claims, secrets.token_hex(16), algorithm="HS256")


def test_find_first_returns_first_match() -> None:
    """`find_first` returns the first item satisfying the predicate."""
    assert find_first(lambda x: x > 2, [1, 2, 3, 4]) == 3


def test_find_first_returns_default_when_no_match() -> None:
    """`find_first` returns the provided default when nothing matches."""
    assert find_first(lambda x: x > 9, [1, 2], default="none") == "none"


def test_compute_daily_expenses_fills_missing_days() -> None:
    """`compute_daily_expenses` derives per-day deltas and carries the previous value forward."""
    from decimal import Decimal

    result = compute_daily_expenses({1: Decimal(10), 3: Decimal(30)}, 3)
    assert result == {1: Decimal(10), 2: Decimal(0), 3: Decimal(20)}


async def test_async_groupby_groups_consecutive_equal_keys() -> None:
    """`async_groupby` yields one group per run of consecutive equal keys."""

    async def _items() -> AsyncIterator[int]:
        for value in [1, 1, 2, 3, 3]:
            yield value

    groups = [(key, list(group)) async for key, group in async_groupby(_items(), key=lambda x: x)]
    assert groups == [(1, [1, 1]), (2, [2]), (3, [3, 3])]


async def test_async_groupby_empty_iterable_yields_nothing() -> None:
    """`async_groupby` yields no groups for an empty async iterable."""

    async def _items() -> AsyncIterator[int]:
        return
        yield  # pragma: no cover

    groups = [item async for item in async_groupby(_items(), key=lambda x: x)]
    assert groups == []


def test_wrap_http_error_in_502_translates_status_error() -> None:
    """`wrap_http_error_in_502` converts an `HTTPStatusError` into a 502 `HTTPException`."""
    response = httpx.Response(503, text="down")
    with pytest.raises(HTTPException) as exc_info:
        with wrap_http_error_in_502("boom"):
            raise httpx.HTTPStatusError("err", request=httpx.Request("GET", "/"), response=response)
    assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY


def test_wrap_http_not_found_in_400_translates_404() -> None:
    """`wrap_http_not_found_in_400` converts a 404 into a 400 `HTTPException`."""
    response = httpx.Response(404)
    with pytest.raises(HTTPException) as exc_info:
        with wrap_http_not_found_in_400("missing"):
            raise httpx.HTTPStatusError("err", request=httpx.Request("GET", "/"), response=response)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_wrap_http_not_found_in_400_reraises_non_404() -> None:
    """`wrap_http_not_found_in_400` re-raises status errors that are not 404."""
    response = httpx.Response(500)
    with pytest.raises(httpx.HTTPStatusError):
        with wrap_http_not_found_in_400("missing"):
            raise httpx.HTTPStatusError("err", request=httpx.Request("GET", "/"), response=response)


def test_wrap_exc_in_http_response_uses_default_message() -> None:
    """`wrap_exc_in_http_response` uses the exception text when no message is supplied."""
    with pytest.raises(HTTPException, match="kaboom") as exc_info:
        with wrap_exc_in_http_response(ValueError):
            raise ValueError("kaboom")
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_wrap_exc_in_http_response_uses_explicit_message() -> None:
    """`wrap_exc_in_http_response` uses the supplied message and status code over the default."""
    with pytest.raises(HTTPException, match="custom") as exc_info:
        with wrap_exc_in_http_response(
            ValueError, error_msg="custom", status_code=status.HTTP_409_CONFLICT
        ):
            raise ValueError("ignored")
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT


def test_get_instance_external_id_skips_short_cpuset_tail(
    monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    """`get_instance_external_id` ignores a non-64-char cpuset tail and tries mountinfo next."""
    get_instance_external_id.cache_clear()
    monkeypatch.setenv("HOSTNAME", "not-hex-host")
    mocker.patch("app.utils.open", mocker.mock_open(read_data="/docker/short"))
    container_id = "c" * 64
    completed = mocker.Mock()
    completed.stdout = f"upperdir=/var/lib/docker/overlay2/{container_id}/diff,x".encode()
    mocker.patch("app.utils.subprocess.run", return_value=completed)
    assert get_instance_external_id() == "c" * 12


def test_get_instance_external_id_skips_short_mountinfo_id(
    monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    """`get_instance_external_id` falls back to a hash when the mountinfo id is not 64 chars."""
    import hashlib

    get_instance_external_id.cache_clear()
    monkeypatch.setenv("HOSTNAME", "not-hex-host")
    mocker.patch("app.utils.open", side_effect=OSError)
    completed = mocker.Mock()
    completed.stdout = b"upperdir=/var/lib/docker/overlay2/short/diff,x"
    mocker.patch("app.utils.subprocess.run", return_value=completed)
    assert get_instance_external_id() == hashlib.sha256(b"not-hex-host").hexdigest()[:12]


def test_get_meta_renders_yaml_to_dict() -> None:
    """`get_meta` renders `meta.yaml` and parses it into a dict containing `events`."""
    meta = get_meta()
    assert isinstance(meta, dict)
    assert "events" in meta


def test_get_jwt_token_claims_decodes_payload() -> None:
    """`get_jwt_token_claims` returns the decoded claim set from a JWT payload."""
    token = _make_jwt({"sub": "USR-1", "role": "admin"})
    claims = get_jwt_token_claims(token)
    assert claims["sub"] == "USR-1"
    assert claims["role"] == "admin"


def test_get_jwt_token_claims_rejects_malformed_token() -> None:
    """`get_jwt_token_claims` raises `ValueError` for a token that is not three dot-parts."""
    with pytest.raises(ValueError, match="Invalid JWT token"):
        get_jwt_token_claims("not-a-jwt")


def test_get_jwt_token_claims_rejects_non_json_payload() -> None:
    """`get_jwt_token_claims` raises `ValueError` when the payload is not valid JSON."""
    payload = base64.urlsafe_b64encode(b"not json").decode().rstrip("=")
    with pytest.raises(ValueError, match="Invalid JWT token"):
        get_jwt_token_claims(f"header.{payload}.signature")


def test_get_jwt_token_expires_returns_expiry() -> None:
    """`get_jwt_token_expires` returns the `exp` claim as a UTC datetime."""
    expires = datetime.now(UTC) + timedelta(hours=1)
    token = _make_jwt({"exp": int(expires.timestamp())})
    assert get_jwt_token_expires(token) == datetime.fromtimestamp(int(expires.timestamp()), tz=UTC)


def test_get_jwt_token_expires_rejects_token_without_exp() -> None:
    """`get_jwt_token_expires` raises `ValueError` when the token has no `exp` claim."""
    token = _make_jwt({"sub": "USR-1"})
    with pytest.raises(ValueError, match="Invalid JWT token"):
        get_jwt_token_expires(token)


def test_get_instance_external_id_returns_hex_hostname(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`get_instance_external_id` returns the hostname when it is a 12-char hex container id."""
    get_instance_external_id.cache_clear()
    monkeypatch.setenv("HOSTNAME", "abcdef012345")
    assert get_instance_external_id() == "abcdef012345"


def test_get_instance_external_id_reads_cpuset(
    monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    """`get_instance_external_id` falls back to the truncated `/proc/1/cpuset` container id."""
    get_instance_external_id.cache_clear()
    monkeypatch.setenv("HOSTNAME", "not-hex-host")
    container_id = "a" * 64
    mocker.patch("app.utils.open", mocker.mock_open(read_data=f"/docker/{container_id}"))
    assert get_instance_external_id() == "a" * 12


def test_get_instance_external_id_parses_mountinfo(
    monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    """`get_instance_external_id` derives the id from the overlay mountinfo when cpuset fails."""
    get_instance_external_id.cache_clear()
    monkeypatch.setenv("HOSTNAME", "not-hex-host")
    mocker.patch("app.utils.open", side_effect=OSError)
    container_id = "b" * 64
    completed = mocker.Mock()
    completed.stdout = f"upperdir=/var/lib/docker/overlay2/{container_id}/diff,lowerdir=x".encode()
    mocker.patch("app.utils.subprocess.run", return_value=completed)
    assert get_instance_external_id() == "b" * 12


def test_get_instance_external_id_hashes_when_no_container_found(
    monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    """`get_instance_external_id` falls back to a 12-char hostname hash when no id is found."""
    import hashlib
    import subprocess

    get_instance_external_id.cache_clear()
    monkeypatch.setenv("HOSTNAME", "not-hex-host")
    mocker.patch("app.utils.open", side_effect=OSError)
    mocker.patch(
        "app.utils.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "grep"),
    )
    expected = hashlib.sha256(b"not-hex-host").hexdigest()[:12]
    assert get_instance_external_id() == expected
