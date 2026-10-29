import re
from datetime import UTC, datetime, timedelta

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.human_readable_pk import HumanReadablePKMixin
from app.db.models import (
    Account,
    ActivityLog,
    Actor,
    ChangeRecord,
    CloudProvider,
    Entitlement,
    Organization,
    System,
)
from app.enums import ActorType, EntitlementStatus
from tests.types import ModelFactory


async def test_actor_inheritance(db_session: AsyncSession):
    # Create a system which inherits from Actor
    account = Account(name="test account", external_id="my_id")
    system = System(name="Test System", external_id="test-system", owner=account)
    db_session.add(account)
    db_session.add(system)
    await db_session.commit()
    await db_session.refresh(system)

    # Query both tables
    actor_result = await db_session.execute(select(Actor).where(Actor.id == system.id))
    system_result = await db_session.execute(select(System).where(System.id == system.id))

    actor = actor_result.scalar_one()
    system_from_db = system_result.scalar_one()

    # Verify inheritance
    assert actor.id == system.id
    assert system.id.startswith("FTKN-")
    assert actor.type == ActorType.SYSTEM
    assert system_from_db.id == system.id
    assert system_from_db.name == system.name


async def test_timestamp_mixin(db_session: AsyncSession):
    org = Organization(
        name="Test Org",
        currency="EUR",
        billing_currency="EUR",
        operations_external_id="test-org",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    assert org.created_at is not None
    assert org.updated_at is not None
    assert isinstance(org.created_at, datetime)
    assert isinstance(org.updated_at, datetime)
    assert org.created_at.tzinfo == UTC
    assert org.updated_at.tzinfo == UTC


async def test_id_mixin(mocker: MockerFixture, db_session: AsyncSession):
    org = Organization(
        name="Test Org",
        currency="EUR",
        billing_currency="EUR",
        operations_external_id="test-org",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    assert org.id is not None
    assert isinstance(org.id, str)
    assert org.id.startswith("FORG-")

    mocker.patch.object(HumanReadablePKMixin, "generate_human_readable_pk", return_value=org.id)
    new_org = Organization(
        name="Test Org",
        currency="EUR",
        billing_currency="EUR",
        operations_external_id="test-org",
    )
    db_session.add(new_org)
    with pytest.raises(
        ValueError,
        match="Unable to generate unique primary key after 15 attempts.",
    ):
        await db_session.commit()


async def test_auditable_mixin(db_session: AsyncSession, ffc_extension: System):
    org = Organization(
        name="Test Org",
        currency="EUR",
        billing_currency="EUR",
        operations_external_id="test-org",
        created_by=ffc_extension,
        updated_by=ffc_extension,
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    # Reload from DB to test relationships
    result = await db_session.execute(select(Organization).where(Organization.id == org.id))
    org_from_db = result.scalar_one()

    assert org_from_db.created_by_id == ffc_extension.id
    assert org_from_db.updated_by_id == ffc_extension.id
    assert org_from_db.created_by.type == ActorType.SYSTEM
    assert org_from_db.updated_by.type == ActorType.SYSTEM


async def test_entitlement_status_default(db_session: AsyncSession):
    account = Account(name="test_account", external_id="my_id")
    entitlement = Entitlement(
        name="AWS",
        affiliate_external_id="ACC-123",
        datasource_id="container-123",
        owner=account,
    )
    db_session.add(account)
    db_session.add(entitlement)
    await db_session.commit()
    await db_session.refresh(entitlement)

    assert entitlement.status == EntitlementStatus.NEW


async def test_organization_unique_external_id(db_session: AsyncSession):
    # Create first organization
    org1 = Organization(
        name="Test Org 1",
        currency="EUR",
        billing_currency="EUR",
        operations_external_id="test-org",
    )
    db_session.add(org1)
    await db_session.commit()
    await db_session.refresh(org1)

    # Try to create another with same external_id
    org2 = Organization(
        name="Test Org 2",
        currency="EUR",
        billing_currency="EUR",
        operations_external_id="test-org",
    )
    db_session.add(org2)

    with pytest.raises(IntegrityError):  # SQLAlchemy will raise an integrity error
        await db_session.flush()


# -- cloud provider --

AWS_FORMAT = r"^[0-9]{12}$"
AZURE_FORMAT = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
PROVIDER_FACTORIES = ["aws_cloud_provider_factory", "azure_cloud_provider_factory"]


@pytest.mark.parametrize(
    ("datasource_id_format", "datasource_id", "expected"),
    [
        pytest.param(AWS_FORMAT, "123456789012", True, id="superman"),
        pytest.param(AWS_FORMAT, "1234567890123", False, id="mr-fantastic"),
        pytest.param(AZURE_FORMAT, "0a1b2c3d-4e5f-6071-8293-a4b5c6d7e8f9", True, id="wonder-woman"),
        pytest.param(AZURE_FORMAT, "0A1B2C3D-4E5F-6071-8293-A4B5C6D7E8F9", False, id="bizarro"),
        pytest.param(AZURE_FORMAT, "spiderman", False, id="spiderman"),
        pytest.param(r"[0-9]{12}", "1234567890123", False, id="hulk"),
        pytest.param(AWS_FORMAT, "", False, id="invisible-woman"),
    ],
)
def test_cloud_provider_matches_datasource_id_requires_a_full_match(
    datasource_id_format: str, datasource_id: str, expected: bool
) -> None:
    """`matches_datasource_id` matches the whole id, even when the pattern has no anchors."""
    provider = CloudProvider(name="Test", icon="aws", datasource_id_format=datasource_id_format)
    assert provider.matches_datasource_id(datasource_id) is expected


@pytest.mark.parametrize("factory_name", PROVIDER_FACTORIES, ids=["aws", "azure"])
async def test_cloud_provider_gets_a_human_readable_id(
    request: pytest.FixtureRequest,
    gcp_account: Account,
    factory_name: str,
) -> None:
    """A persisted provider gets an `FCLP-` id in the shape `build_id_regex` describes."""
    cloud_provider_factory: ModelFactory[CloudProvider] = request.getfixturevalue(factory_name)

    provider = await cloud_provider_factory(gcp_account)

    assert provider.id.startswith(f"{CloudProvider.PK_PREFIX}-")
    assert re.fullmatch(CloudProvider.build_id_regex(), provider.id)
    assert gcp_account.cloud_provider is provider


@pytest.mark.parametrize("factory_name", PROVIDER_FACTORIES, ids=["aws", "azure"])
async def test_cloud_provider_is_unique_per_account(
    request: pytest.FixtureRequest,
    gcp_account: Account,
    db_session: AsyncSession,
    factory_name: str,
) -> None:
    """A second provider for the same account violates `uq_cloud_providers_account_id`."""
    cloud_provider_factory: ModelFactory[CloudProvider] = request.getfixturevalue(factory_name)
    await cloud_provider_factory(gcp_account)

    # Set the foreign key, not the relationship: assigning `account=` would make the
    # one-to-one backref detach the first provider instead of inserting a second one.
    db_session.add(
        CloudProvider(
            account_id=gcp_account.id, name="Second", icon="aws", datasource_id_format=".*"
        )
    )
    with pytest.raises(IntegrityError, match="uq_cloud_providers_account_id"):
        await db_session.commit()


# -- activity log --


async def test_activity_log_gets_a_human_readable_id(
    activity_log_factory: ModelFactory[ActivityLog],
) -> None:
    """A persisted activity log gets an `FLOG-` id in the shape `build_id_regex` describes."""
    activity_log = await activity_log_factory()

    assert activity_log.id.startswith(f"{ActivityLog.PK_PREFIX}-")
    assert re.fullmatch(ActivityLog.build_id_regex(), activity_log.id)


async def test_activity_log_timestamp_defaults_to_now_in_utc(
    activity_log_factory: ModelFactory[ActivityLog],
) -> None:
    """An activity log created without a timestamp is stamped with the current UTC time."""
    before = datetime.now(UTC)

    activity_log = await activity_log_factory()

    assert activity_log.timestamp.tzinfo == UTC
    assert before <= activity_log.timestamp <= datetime.now(UTC)


async def test_activity_log_keeps_an_explicit_timestamp(
    activity_log_factory: ModelFactory[ActivityLog],
) -> None:
    """A timestamp given on creation is stored as is, so past activities can be recorded."""
    happened_at = datetime.now(UTC) - timedelta(days=3)

    activity_log = await activity_log_factory(timestamp=happened_at)

    assert activity_log.timestamp == happened_at


async def test_activity_log_requires_an_actor(db_session: AsyncSession) -> None:
    """An activity log cannot be persisted without the actor that performed it."""
    db_session.add(ActivityLog(action="organization.updated", message="Renamed"))

    with pytest.raises(IntegrityError, match='null value in column "actor_id"'):
        await db_session.commit()


async def test_activity_log_links_the_actor(
    db_session: AsyncSession,
    ffc_extension: System,
    activity_log_factory: ModelFactory[ActivityLog],
) -> None:
    """An eagerly loaded activity log exposes the actor that performed the activity."""
    activity_log = await activity_log_factory(actor=ffc_extension)
    db_session.expunge_all()

    loaded = await db_session.scalar(
        select(ActivityLog)
        .options(selectinload(ActivityLog.actor))
        .where(ActivityLog.id == activity_log.id)
    )

    assert loaded is not None
    assert loaded.actor.id == ffc_extension.id


@pytest.mark.parametrize("relationship_name", ["actor", "changes"])
async def test_activity_log_relationships_are_not_lazy_loaded(
    db_session: AsyncSession,
    activity_log_factory: ModelFactory[ActivityLog],
    relationship_name: str,
) -> None:
    """Accessing a relationship that was not eagerly loaded raises instead of querying."""
    activity_log = await activity_log_factory()
    db_session.expunge_all()
    loaded = await db_session.scalar(select(ActivityLog).where(ActivityLog.id == activity_log.id))
    assert loaded is not None

    with pytest.raises(InvalidRequestError, match="lazy='raise'"):
        getattr(loaded, relationship_name)


async def test_change_record_gets_a_human_readable_id(
    change_record_factory: ModelFactory[ChangeRecord],
) -> None:
    """A persisted change record gets an `FCHG-` id in the shape `build_id_regex` describes."""
    change_record = await change_record_factory()

    assert change_record.id.startswith(f"{ChangeRecord.PK_PREFIX}-")
    assert re.fullmatch(ChangeRecord.build_id_regex(), change_record.id)


async def test_change_record_stores_json_snapshots(
    db_session: AsyncSession,
    change_record_factory: ModelFactory[ChangeRecord],
) -> None:
    """`before` and `after` round-trip as JSON, with `before` null for a created object."""
    change_record = await change_record_factory(before=None, after={"name": "Acme", "users": 3})
    db_session.expunge_all()

    loaded = await db_session.scalar(
        select(ChangeRecord).where(ChangeRecord.id == change_record.id)
    )

    assert loaded is not None
    assert loaded.before is None
    assert loaded.after == {"name": "Acme", "users": 3}


async def test_change_record_requires_an_activity_log(db_session: AsyncSession) -> None:
    """A change record cannot be persisted without its parent activity log."""
    db_session.add(ChangeRecord(object_type="organization", object_id="FORG-0001", after={}))

    with pytest.raises(IntegrityError, match='null value in column "activity_log_id"'):
        await db_session.commit()


async def test_activity_log_lists_its_change_records(
    db_session: AsyncSession,
    activity_log_factory: ModelFactory[ActivityLog],
    change_record_factory: ModelFactory[ChangeRecord],
) -> None:
    """An eagerly loaded activity log exposes every change record written for it."""
    activity_log = await activity_log_factory()
    first = await change_record_factory(activity_log=activity_log, object_type="organization")
    second = await change_record_factory(activity_log=activity_log, object_type="entitlement")
    db_session.expunge_all()

    loaded = await db_session.scalar(
        select(ActivityLog)
        .options(selectinload(ActivityLog.changes))
        .where(ActivityLog.id == activity_log.id)
    )

    assert loaded is not None
    assert {change.id for change in loaded.changes} == {first.id, second.id}


async def test_deleting_an_activity_log_deletes_its_change_records(
    db_session: AsyncSession,
    activity_log_factory: ModelFactory[ActivityLog],
    change_record_factory: ModelFactory[ChangeRecord],
) -> None:
    """Deleting an activity log cascades to its change records."""
    activity_log = await activity_log_factory()
    await change_record_factory(activity_log=activity_log)
    db_session.expunge_all()
    loaded = await db_session.get(ActivityLog, activity_log.id)
    assert loaded is not None

    await db_session.delete(loaded)
    await db_session.commit()

    remaining = await db_session.scalars(select(ChangeRecord))
    assert remaining.all() == []
