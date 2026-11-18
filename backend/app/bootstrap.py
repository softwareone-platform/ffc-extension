import json
import logging
import pathlib

import httpx
from mrok.agent import ziticorn
from sqlalchemy import create_engine, select

from app.conf import Settings
from app.db.models import Account
from app.enums import AccountStatus, AccountType
from app.logging import get_logging_config
from app.utils import get_instance_external_id, get_meta

logger = logging.getLogger(__name__)


def get_affiliate_products(settings: Settings) -> list[str]:
    """
    Loads the products of the active affiliate accounts.

    `bootstrap` runs before any event loop exists, so the database is read through a
    short-lived synchronous engine, disposed before the server workers are started.

    Args:
        settings (Settings): the application settings.

    Returns:
        list[str]: the sorted, unique product ids.
    """
    engine = create_engine(str(settings.postgres_url))
    try:
        with engine.connect() as connection:
            rows = connection.scalars(
                select(Account.products).where(
                    Account.type == AccountType.AFFILIATE,
                    Account.status == AccountStatus.ACTIVE,
                    Account.products.is_not(None),
                )
            ).all()
    finally:
        engine.dispose()

    return sorted(
        {product.strip() for row in rows for product in row.split(",") if product.strip()}
    )


def bootstrap(
    settings: Settings,
    ziti_load_timeout_ms: int = 5000,
    server_workers: int = 4,
    server_reload: bool = False,
    server_backlog: int = 2048,
    server_timeout_keep_alive: int = 5,
    server_limit_concurrency: int | None = None,
    server_limit_max_requests: int | None = None,
    events_publishers_port: int = 50000,
    events_subscribers_port: int = 50001,
    events_metrics_collect_interval: float = 5.0,
):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.mpt_extension_token}",
    }

    external_id = get_instance_external_id()
    identity_file = (
        pathlib.Path(__file__).parent.parent.parent.resolve() / f"{external_id}_identity.json"
    )
    logger.info(
        f"Boostrap instance for extension {settings.mpt_extension_id}: externalId={external_id}",
    )

    data = {
        "externalId": external_id,
        "meta": get_meta(products=get_affiliate_products(settings)),
    }
    for evtinfo in data["meta"]["events"]:
        msg = (
            f"Register event subscription to {evtinfo['event']} "
            f"(task={evtinfo['task']}, filter={evtinfo.get('filter', '-')}) "
            f"-> {evtinfo['path']}"
        )
        logger.info(msg)

    if not identity_file.exists():
        logger.info(
            f"Request new identity for {settings.mpt_extension_id}: externalId={external_id}",
        )
        data["channel"] = {}
    else:
        identity = json.load(open(identity_file))
        identity_extension = identity.get("mrok", {}).get("extension", "")
        if identity_extension.lower() != settings.mpt_extension_id.lower():
            logger.warning(
                f"The existing identity belongs to the extension {identity_extension}. "
                f"Request new identity for {settings.mpt_extension_id}: externalId={external_id}",
            )
            data["channel"] = {}

    response = httpx.post(
        f"{settings.mpt_api_base_url}/integration/extensions/{settings.mpt_extension_id}/instances",
        headers=headers,
        json=data,
        timeout=httpx.Timeout(connect=1.0, pool=1.0, read=180.0, write=30.0),
    )
    response.raise_for_status()
    response_data = response.json()
    identity = response_data.get("channel", {}).get("identity")
    if identity:
        logger.info(f"Save instance identity to {identity_file}")
        with open(identity_file, "w") as writer:
            json.dump(identity, writer)
    logger.info(
        f"Instance bootstrap for extension {settings.mpt_extension_id} completed: "
        f"{response_data['id']}"
    )
    ziticorn.run(
        "app.main:app",
        str(identity_file),
        ziti_load_timeout_ms=ziti_load_timeout_ms,
        server_workers=server_workers,
        server_reload=server_reload,
        server_backlog=server_backlog,
        server_timeout_keep_alive=server_timeout_keep_alive,
        server_limit_concurrency=server_limit_concurrency,
        server_limit_max_requests=server_limit_max_requests,
        events_metrics_collect_interval=events_metrics_collect_interval,
        events_publishers_port=events_publishers_port,
        events_subscribers_port=events_subscribers_port,
        logging_config=get_logging_config(settings),
    )
