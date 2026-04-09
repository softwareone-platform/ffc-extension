import base64
import binascii
import contextlib
import json
import logging
import os
import smtplib
import uuid
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

import httpx
from fastapi import HTTPException, status
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.conf import Settings

logger = logging.getLogger(__name__)


def dateformat(date_obj: datetime | None) -> str:
    return date_obj.strftime("%-d %B %Y") if date_obj else ""


env = Environment(
    loader=FileSystemLoader(
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "templates",
            "emails",
        ),
    ),
    autoescape=select_autoescape(),
)

env.filters["dateformat"] = dateformat


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


def send_email(
    settings: Settings, recipient_email: str, recipient_name: str, subject: str, message: str
) -> None:
    sender_email = settings.smtp_sender_email
    sender_name = settings.smtp_sender_name

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((sender_name, sender_email))
    msg["To"] = formataddr((recipient_name, recipient_email))

    html_part = MIMEText(message, "html")
    msg.attach(html_part)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())


def generate_invitation_email(id: str, name: str, token: str, expires: datetime):
    template = env.get_template("invitation.html.j2")
    return template.render(
        id=id,
        name=name,
        token=token,
        expires=expires,
    )


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
    except (KeyError, ValueError, json.JSONDecodeError, binascii.Error) as exc:
        raise ValueError("Invalid JWT token") from exc


def get_jwt_token_expires(token: str) -> datetime:
    try:
        claims = get_jwt_token_claims(token)
        return datetime.fromtimestamp(claims["exp"], tz=UTC)
    except (KeyError, ValueError) as exc:
        raise ValueError("Invalid JWT token") from exc
