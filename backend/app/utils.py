import base64
import binascii
import contextlib
import hashlib
import json
import logging
import os
import socket
import subprocess
from datetime import UTC, datetime
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

import httpx
from fastapi import HTTPException, status
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from yaml import safe_load

from app.conf import get_settings

logger = logging.getLogger(__name__)

_JINJA_ENV = Environment(  # noqa: S701
    loader=FileSystemLoader(Path(__file__).parent.parent.parent.resolve()),
    undefined=StrictUndefined,
)


def find_first(func, iterable, default=None):
    return next(filter(func, iterable), default)


def compute_daily_expenses(
    cumulative_expenses: dict[int, Decimal], last_day_of_month: int
) -> dict[int, Decimal]:
    """
    This function computes the daily expenses based on the given cumulative expenses.
    It also fills in any missing days using the previous days' cumulative value.
    Args:
        cumulative_expenses: dict[int,Decimal]: the original cumulative expenses dictionary
        last_day_of_month: the last day of the month
    Returns:
        daily_expenses: dict[int,Decimal]: the daily expenses dictionary
    """
    daily_expenses = {}
    previous_amount = Decimal(0)
    for day in range(1, last_day_of_month + 1):
        current = Decimal(cumulative_expenses.get(day, previous_amount))
        daily_expenses[day] = Decimal(current - previous_amount)
        previous_amount = current
    return daily_expenses


async def async_groupby(
    iterable,
    key,
):
    current_group = []
    current_key = None
    first_item = True

    async for item in iterable:
        k = key(item)
        if first_item:
            current_key = k
            current_group.append(item)
            first_item = False
        elif k == current_key:
            current_group.append(item)
        else:
            yield current_key, current_group
            current_key = k
            current_group = [item]

    if current_group:
        yield current_key, current_group


@contextlib.contextmanager
def wrap_http_error_in_502(base_msg: str = "Error in FinOps for Cloud"):
    try:
        yield
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{base_msg}: {e.response.status_code} - {e.response.text}.",
        ) from e


@contextlib.contextmanager
def wrap_http_not_found_in_400(message: str):
    try:
        yield
    except httpx.HTTPStatusError as e:
        if e.response.status_code != httpx.codes.NOT_FOUND:
            raise
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from e


@contextlib.contextmanager
def wrap_exc_in_http_response(
    exc_cls: type[Exception],
    error_msg: str | None = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
):
    try:
        yield
    except exc_cls as e:
        if error_msg is None:
            error_msg = str(e)

        logger.exception(
            f"{exc_cls.__name__} error was raised during an operation, "
            f"returning a {status_code} HTTP response: {error_msg}"
        )
        raise HTTPException(status_code=status_code, detail=error_msg) from e


def _extract_container_id_from_cpuset(cpuset_content: str) -> str | None:
    container_id = cpuset_content.strip().rsplit("/", 1)[-1]
    if len(container_id) == 64:
        return container_id[:12]
    return None


@lru_cache(maxsize=1)
def get_instance_external_id() -> str:
    hostname = (os.environ.get("HOSTNAME") or socket.gethostname() or "").lower()
    if len(hostname) == 12 and all(c in "0123456789abcdef" for c in hostname.lower()):
        return hostname

    try:
        with open("/proc/1/cpuset") as f:
            tail = f.read().strip().rsplit("/", 1)[-1]
        if len(tail) == 64:
            return tail[:12]
    except OSError:
        pass

    try:
        result = subprocess.run(  # noqa: S603
            ["grep", "overlay", "/proc/self/mountinfo"],  # noqa: S607
            capture_output=True,
            stdin=subprocess.DEVNULL,
            check=True,
        )
        mount = result.stdout.decode()
        start = mount.index("upperdir=") + len("upperdir=")
        end = mount.index(",", start)
        cid = mount[start:end].rsplit("/", 2)[1]
        if len(cid) == 64:
            return cid[:12]
    except (subprocess.CalledProcessError, ValueError, OSError):
        pass

    seed = hostname or os.environ.get("HOSTNAME", "") or "unknown-host"
    return hashlib.sha256(seed.encode()).hexdigest()[:12]


def get_meta():
    template = _JINJA_ENV.get_template("meta.yaml")
    return safe_load(template.render(settings=get_settings()))


def get_jwt_token_claims(token: str) -> dict:
    try:
        _, payload, _ = token.split(".")

        # Add padding if needed
        padding = "=" * (-len(payload) % 4)
        payload += padding

        decoded = base64.urlsafe_b64decode(payload)
        claims = json.loads(decoded)
        return claims
    except (KeyError, ValueError, json.JSONDecodeError, binascii.Error) as exc:
        raise ValueError("Invalid JWT token") from exc


def get_jwt_token_expires(token: str) -> datetime:
    try:
        claims = get_jwt_token_claims(token)
        return datetime.fromtimestamp(claims["exp"], tz=UTC)
    except (KeyError, ValueError) as exc:
        raise ValueError("Invalid JWT token") from exc
