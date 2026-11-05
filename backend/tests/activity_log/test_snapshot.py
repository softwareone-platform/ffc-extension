from sqlalchemy.ext.asyncio import AsyncSession

from app.activity_log import MASK, snapshot
from app.db.models import Organization
from app.enums import OrganizationStatus
from tests.types import ModelFactory


async def test_snapshot_returns_every_loaded_column(
    organization_factory: ModelFactory[Organization],
) -> None:
    """`snapshot()` contains one key per column, with the stored values."""
    organization = await organization_factory(name="Acme", currency="EUR")

    data = snapshot(organization)

    assert data["id"] == organization.id
    assert data["name"] == "Acme"
    assert data["currency"] == "EUR"
    assert set(data) == {attr.key for attr in Organization.__mapper__.column_attrs}


async def test_snapshot_values_are_json_safe(
    organization_factory: ModelFactory[Organization],
) -> None:
    """Enums become their value and datetimes become ISO strings."""
    organization = await organization_factory(status=OrganizationStatus.ACTIVE)

    data = snapshot(organization)

    assert data["status"] == "active"
    assert isinstance(data["created_at"], str)
    assert data["created_at"] == organization.created_at.isoformat()


async def test_snapshot_masks_sensitive_columns(
    organization_factory: ModelFactory[Organization], sensitive_column: str
) -> None:
    """A column declared with `info={"sensitive": True}` is written as the mask."""
    organization = await organization_factory(operations_external_id="AGR-SECRET")

    data = snapshot(organization)

    assert data[sensitive_column] == MASK


async def test_snapshot_skips_expired_attributes(
    organization_factory: ModelFactory[Organization], db_session: AsyncSession
) -> None:
    """An expired attribute is left out instead of being lazy-loaded."""
    organization = await organization_factory()
    db_session.expire(organization, ["name"])

    data = snapshot(organization)

    assert "name" not in data
    assert "id" in data


def test_snapshot_of_transient_object_has_only_assigned_values() -> None:
    """An object never flushed exposes only the attributes that were set on it."""
    organization = Organization(name="Acme", currency="EUR")

    data = snapshot(organization)

    assert data == {"name": "Acme", "currency": "EUR"}
