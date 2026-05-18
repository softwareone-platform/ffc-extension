import base64
import contextlib
import json
import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import httpx
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


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


def _extract_container_id_from_mountinfo(mountinfo_content: str) -> str | None:
    for line in mountinfo_content.splitlines():
        if "upperdir=" not in line:
            continue
        start_idx = line.index("upperdir=") + len("upperdir=")
        end_idx = line.find(",", start_idx)
        dir_path = line[start_idx:] if end_idx == -1 else line[start_idx:end_idx]
        parts = dir_path.rsplit("/", 2)
        if len(parts) != 3:
            continue
        container_id = parts[1]
        if len(container_id) == 64:
            return container_id[:12]
    return None


def get_instance_external_id() -> str:
    try:
        cpuset_content = Path("/proc/1/cpuset").read_text(encoding="utf-8")
        cpuset_id = _extract_container_id_from_cpuset(cpuset_content)
        if cpuset_id is not None:
            return cpuset_id
    except OSError:
        pass

    try:
        mountinfo_content = Path("/proc/self/mountinfo").read_text(encoding="utf-8")
        mountinfo_id = _extract_container_id_from_mountinfo(mountinfo_content)
        if mountinfo_id is not None:
            return mountinfo_id
    except OSError:
        pass

    return f"{uuid.getnode():012x}"


def get_jwt_token_claims(token: str) -> dict:
    try:
        _, payload, _ = token.split(".")

        # Add padding if needed
        padding = "=" * (-len(payload) % 4)
        payload += padding

        decoded = base64.urlsafe_b64decode(payload)
        claims = json.loads(decoded)
        return claims
    except (KeyError, ValueError) as exc:
        raise ValueError("Invalid JWT token") from exc


def get_jwt_token_expires(token: str) -> datetime:
    try:
        claims = get_jwt_token_claims(token)
        return datetime.fromtimestamp(claims["exp"], tz=UTC)
    except (KeyError, ValueError) as exc:
        raise ValueError("Invalid JWT token") from exc
