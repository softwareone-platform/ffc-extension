import asyncio
import logging

import typer
from httpx import HTTPStatusError, ReadTimeout

from app.api_clients.ffc_api import FFCAPIClient
from app.conf import Settings
from app.db.base import session_factory
from app.db.handlers import EntitlementHandler
from app.db.models import Entitlement
from app.enums import EntitlementStatus
from app.telemetry import capture_telemetry_cli_command

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


@capture_telemetry_cli_command(__name__, "Set Entitlements tag")
async def set_entitlements_tag(settings: Settings):
    tags_to_set = {}
    async with session_factory.begin() as session:
        entitlement_handler = EntitlementHandler(session)
        ffc_api_client = FFCAPIClient(settings)

        async for entitlements in entitlement_handler.stream_scalars_in_batches(
            extra_conditions=[Entitlement.status == EntitlementStatus.ACTIVE],
            batch_size=BATCH_SIZE,
        ):
            logger.info("Fetching tags for entitlements")
            entitlements_map = {ent.id: ent.linked_datasource_id for ent in entitlements}

            try:
                entitlement_ids = ",".join(entitlements_map)
                rql = f"and(eq(name,entitlement),in(value,({entitlement_ids})))"
                response = await ffc_api_client.get_tags(rql=rql, limit=BATCH_SIZE)
            except (HTTPStatusError, ReadTimeout) as exc:
                logger.warning(f"Error getting tags: {exc}")
                continue

            tags = response.json()["items"]
            for tag in tags:
                if tag["value"] in entitlements_map:
                    del entitlements_map[tag["value"]]

            tags_to_set.update(entitlements_map)

            logger.info(f"Found {len(entitlements_map)} tags to set")

    created_tags = 0
    for entitlement_id, datasource_id in tags_to_set.items():
        try:
            await ffc_api_client.create_tag_for_datasource(
                datasource_id=datasource_id,
                name="entitlement",
                value=entitlement_id,
            )
            created_tags += 1
        except (HTTPStatusError, ReadTimeout) as exc:
            logger.warning(f"Error creating tag for {entitlement_id}: {exc}")

    logger.info(f"Created {created_tags}/{len(tags_to_set)} tags")


def command(ctx: typer.Context):
    """Set missing tag for active entitlement."""
    asyncio.run(set_entitlements_tag(ctx.obj))
