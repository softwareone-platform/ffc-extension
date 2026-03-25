from datetime import UTC, datetime

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.human_readable_pk import HumanReadablePKMixin
from app.db.models import Account, Actor, Entitlement, Organization, System
from app.enums import ActorType, EntitlementStatus


async def test_actor_inheritance(db_session: AsyncSession):
    # Create a system which inherits from Actor
    account = Account(name="test account", external_id="my_id")
    system = System(
        name="Test System", external_id="test-system", jwt_secret="secret", owner=account
    )
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


async def test_system_encrypted_jwt_secret(db_session: AsyncSession):
    secret = "test-secret"
    account = Account(name="Test account", external_id="my_id")
    system = System(name="Test System", external_id="test-system", jwt_secret=secret, owner=account)
    db_session.add(account)
    db_session.add(system)
    await db_session.commit()
    await db_session.refresh(system)

    # Reload from DB
    result = await db_session.execute(select(System).where(System.id == system.id))
    system_from_db = result.scalar_one()

    # Secret should be encrypted in DB but decrypted when accessed
    assert system_from_db.jwt_secret == secret
