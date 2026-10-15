import re
from datetime import UTC, datetime

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.human_readable_pk import HumanReadablePKMixin
from app.db.models import Account, Actor, CloudProvider, Entitlement, Organization, System
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
