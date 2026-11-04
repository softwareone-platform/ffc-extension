from sqlalchemy.ext.asyncio import AsyncSession

from app.activity_log.constants import MASK
from app.activity_log.snapshot import before_image, snapshot
from app.db.models import Organization
from app.enums import OrganizationStatus
from tests.types import ModelFactory


async def test_snapshot_returns_loaded_columns_as_json(
    organization_factory: ModelFactory[Organization],
) -> None:
    """`snapshot()` returns every loaded column of an instance in a JSON-safe form."""
    organization = await organization_factory(name="Apple Inc.", status=OrganizationStatus.ACTIVE)

    data = snapshot(organization)

    assert data["id"] == organization.id
    assert data["name"] == "Apple Inc."
    assert data["status"] == "active"
    assert data["created_at"] == organization.created_at.isoformat()


async def test_snapshot_skips_attributes_that_are_not_loaded(
    db_session: AsyncSession, organization_factory: ModelFactory[Organization]
) -> None:
    """`snapshot()` leaves out expired attributes instead of lazy-loading them."""
    organization = await organization_factory()
    db_session.expire(organization, ["name"])

    data = snapshot(organization)

    assert "name" not in data
    assert data["id"] == organization.id


async def test_snapshot_masks_sensitive_columns(
    organization_factory: ModelFactory[Organization], sensitive_column: str
) -> None:
    """`snapshot()` masks the value of a column flagged `info={"sensitive": True}`."""
    organization = await organization_factory(operations_external_id="AGR-0000-0000-0001")

    assert snapshot(organization)[sensitive_column] == MASK


async def test_before_image_restores_the_value_before_the_pending_change(
    organization_factory: ModelFactory[Organization],
) -> None:
    """`before_image()` overlays the previous value of attributes changed but not yet flushed."""
    organization = await organization_factory(name="Before")
    organization.name = "After"

    assert before_image(organization)["name"] == "Before"
    assert snapshot(organization)["name"] == "After"


async def test_before_image_masks_sensitive_previous_values(
    organization_factory: ModelFactory[Organization], sensitive_column: str
) -> None:
    """`before_image()` masks the previous value of a sensitive column as well."""
    organization = await organization_factory(operations_external_id="AGR-0000-0000-0001")
    organization.operations_external_id = "AGR-0000-0000-0002"

    assert before_image(organization)[sensitive_column] == MASK
