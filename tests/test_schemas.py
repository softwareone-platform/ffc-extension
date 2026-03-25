import secrets
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.db.models import Account, Actor, Entitlement, Organization, System
from app.enums import AccountType, ActorType, EntitlementStatus, OrganizationStatus, SystemStatus
from app.schemas.core import ActorRead, convert_model_to_schema, convert_schema_to_model
from app.schemas.entitlements import EntitlementCreate, EntitlementRead, EntitlementUpdate
from app.schemas.organizations import (
    OrganizationBase,
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)
from app.schemas.systems import SystemCreate, SystemRead


def test_actor_read_convert_model_to_schema():
    test_actor = Actor(
        id="OPE-1234-5678",
        type=ActorType.USER,
    )
    actor_read = convert_model_to_schema(ActorRead, test_actor)

    assert actor_read.id == test_actor.id
    assert actor_read.type == test_actor.type


def test_system_create_convert_schema_to_model():
    data = {
        "name": "Test System",
        "external_id": "test-system",
        "jwt_secret": secrets.token_urlsafe(64),
        "description": "Test Description",
        "owner": {"id": "FACC-1234-5678"},
    }

    system_create = SystemCreate(**data)
    system = convert_schema_to_model(system_create, System)

    assert isinstance(system, System)
    assert system.name == data["name"]
    assert system.external_id == data["external_id"]
    assert system.jwt_secret == data["jwt_secret"]
    assert system.description == data["description"]
    assert system.type == ActorType.SYSTEM


def test_system_read_convert_model_to_schema(gcp_extension: System):
    system = System(
        id="FTKN-1234-5678",
        name="Test System",
        external_id="test-system",
        jwt_secret=secrets.token_urlsafe(64),
        description="Test Description",
        type=ActorType.SYSTEM,
        status=SystemStatus.ACTIVE,
        owner=Account(id="FACC-1234-5678", name="test", type=AccountType.AFFILIATE),
    )
    system.created_at = datetime.now(UTC)
    system.updated_at = datetime.now(UTC)
    system.created_by = gcp_extension
    system.updated_by = gcp_extension

    system_read = convert_model_to_schema(SystemRead, system)

    assert system_read.id == system.id
    assert system_read.name == system.name
    assert system_read.external_id == system.external_id
    assert system_read.description == system.description
    assert system_read.events.created.at == system.created_at
    assert system_read.events.updated.at == system.updated_at
    assert system_read.events.created.by is not None
    assert system_read.events.created.by.id == gcp_extension.id
    assert system_read.events.updated.by is not None
    assert system_read.events.updated.by.id == gcp_extension.id
    assert system_read.owner.id == system.owner.id


def test_entitlement_create_convert_schema_to_model():
    data = {
        "name": "AWS",
        "affiliate_external_id": "ACC-123",
        "datasource_id": "container-123",
    }

    entitlement_create = EntitlementCreate(**data)
    entitlement = convert_schema_to_model(entitlement_create, Entitlement)

    assert isinstance(entitlement, Entitlement)
    assert entitlement.name == data["name"]
    assert entitlement.affiliate_external_id == data["affiliate_external_id"]
    assert entitlement.datasource_id == data["datasource_id"]


@pytest.mark.parametrize("set_redeemed", [True, False])
@pytest.mark.parametrize("set_terminated", [True, False])
def test_entitlement_read_convert_model_to_schema(
    gcp_extension: System,
    affiliate_account: Account,
    set_terminated: bool,
    set_redeemed: bool,
):
    entitlement = Entitlement(
        id="FENT-1234-5678-9012",
        name="AWS",
        affiliate_external_id="ACC-123",
        datasource_id="container-123",
        status=EntitlementStatus.ACTIVE,
        owner=affiliate_account,
    )
    # Set timestamps and audit fields after creation
    entitlement.created_at = datetime.now(UTC)
    entitlement.updated_at = datetime.now(UTC)
    entitlement.created_by = gcp_extension
    entitlement.updated_by = gcp_extension

    if set_terminated:
        entitlement.terminated_at = datetime.now(UTC)
        entitlement.terminated_by = gcp_extension

    if set_redeemed:
        redeeemer_organization = Organization(
            id="FORG-1234-5678-9012",
            name="Test Org",
            currency="EUR",
            billing_currency="EUR",
            linked_organization_id="ORG-123",
            operations_external_id="FFC-123",
            status=OrganizationStatus.ACTIVE,
        )

        entitlement.redeemed_at = datetime.now(UTC)
        entitlement.redeemed_by = redeeemer_organization

    entitlement_read = convert_model_to_schema(EntitlementRead, entitlement)

    assert entitlement_read.id == entitlement.id
    assert entitlement_read.name == entitlement.name
    assert entitlement_read.affiliate_external_id == entitlement.affiliate_external_id
    assert entitlement_read.datasource_id == entitlement.datasource_id
    assert entitlement_read.status == entitlement.status
    assert entitlement_read.events.created.at == entitlement.created_at
    assert entitlement_read.events.updated.at == entitlement.updated_at
    assert entitlement_read.events.created.by is not None
    assert entitlement_read.events.created.by.id == gcp_extension.id
    assert entitlement_read.events.created.by.type == gcp_extension.type
    assert entitlement_read.events.created.by.name == gcp_extension.name
    assert entitlement_read.events.updated.by is not None
    assert entitlement_read.events.updated.by.id == gcp_extension.id
    assert entitlement_read.events.updated.by.type == gcp_extension.type
    assert entitlement_read.events.updated.by.name == gcp_extension.name

    if set_terminated:
        assert entitlement_read.events.terminated is not None

        assert entitlement_read.events.terminated.at == entitlement.terminated_at
        assert entitlement_read.events.terminated.by is not None
        assert entitlement_read.events.terminated.by.id == gcp_extension.id
        assert entitlement_read.events.terminated.by.type == gcp_extension.type
        assert entitlement_read.events.terminated.by.name == gcp_extension.name
    else:
        assert entitlement_read.events.terminated is None

    if set_redeemed:
        assert entitlement_read.events.redeemed is not None

        assert entitlement_read.events.redeemed.at == entitlement.redeemed_at
        assert entitlement_read.events.redeemed.by is not None
        assert entitlement_read.events.redeemed.by.id == redeeemer_organization.id
        assert entitlement_read.events.redeemed.by.name == redeeemer_organization.name
        assert (
            entitlement_read.events.redeemed.by.operations_external_id
            == redeeemer_organization.operations_external_id
        )
    else:
        assert entitlement_read.events.redeemed is None


def test_entitlement_update_partial():
    update_data = {
        "name": "Updated AWS",
    }

    entitlement_update = EntitlementUpdate(**update_data)
    data = entitlement_update.model_dump(exclude_unset=True)

    assert len(data) == 1
    assert data["name"] == update_data["name"]


def test_organization_create_convert_schema_to_model():
    data = {
        "name": "Test Org",
        "operations_external_id": "ORG-123",
        "user_id": "user-123",
        "currency": "USD",
        "billing_currency": "EUR",
    }

    org_create = OrganizationCreate(**data)
    organization = convert_schema_to_model(org_create, Organization)

    assert isinstance(organization, Organization)
    assert organization.name == data["name"]
    assert organization.operations_external_id == data["operations_external_id"]
    # These fields should not be in the ORM model
    assert not hasattr(organization, "user_id")


def test_organization_read_convert_model_to_schema(ffc_extension: System):
    organization = Organization(
        id="FORG-1234-5678-9012",
        name="Test Org",
        currency="EUR",
        billing_currency="EUR",
        operations_external_id="ORG-123",
        linked_organization_id="FFC-123",
        status=OrganizationStatus.ACTIVE,
    )
    # Set timestamps and audit fields after creation
    organization.created_at = datetime.now(UTC)
    organization.updated_at = datetime.now(UTC)
    organization.created_by = ffc_extension
    organization.updated_by = ffc_extension

    org_read = convert_model_to_schema(OrganizationRead, organization)

    assert org_read.id == organization.id
    assert org_read.name == organization.name
    assert org_read.currency == organization.currency
    assert org_read.operations_external_id == organization.operations_external_id
    assert org_read.linked_organization_id == organization.linked_organization_id
    assert org_read.status == organization.status
    assert org_read.events.created.at == organization.created_at
    assert org_read.events.updated.at == organization.updated_at
    assert org_read.events.created.by is not None
    assert org_read.events.created.by.id == ffc_extension.id
    assert org_read.events.created.by.type == ffc_extension.type
    assert org_read.events.created.by.name == ffc_extension.name
    assert org_read.events.updated.by is not None
    assert org_read.events.updated.by.id == ffc_extension.id
    assert org_read.events.updated.by.type == ffc_extension.type
    assert org_read.events.updated.by.name == ffc_extension.name


def test_organization_update_partial():
    update_data = {
        "name": "Updated Org",
        "operations_external_id": "FFC-456",
    }

    org_update = OrganizationUpdate(**update_data)
    data = org_update.model_dump(exclude_unset=True)

    assert len(data) == 2
    assert data["name"] == update_data["name"]
    assert data["operations_external_id"] == update_data["operations_external_id"]


@pytest.mark.parametrize("currency", ["XTS", "XXX", "XYZ"])
def test_organization_invalid_currencies(currency):
    with pytest.raises(ValidationError) as ce:
        OrganizationBase(
            name="My Org",
            currency=currency,
            billing_currency="USD",
            operations_external_id="EXT-ID",
        )
    errors = ce.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("currency",)
    assert str(errors[0]["ctx"]["error"]) == f"Invalid iso4217 currency code: {currency}."


@pytest.mark.parametrize(
    "currency",
    [
        "XAU",  # gold
        "XAG",  # silver
        "XPD",  # palladium
        "XPT",  # platinum
        "XBA",  # European Composite Unit (EURCO) (bond market unit)
        "XBB",  # European Monetary Unit (E.M.U.-6) (bond market unit)
        "XBC",  # European Unit of Account 9 (E.U.A.-9) (bond market unit)
        "XBD",  # European Unit of Account 17 (E.U.A.-17) (bond market unit)
        "XDR",  # Special drawing rights (International Monetary Fund)
        "XSU",  # Unified System for Regional Compensation (SUCRE)
        "XTS",  # reserved for testign
        "XXX",  # No currency
        "XUX",  # doesn't exist,
        "XYZ",  # also doesn't exit :)
    ],
)
def test_organization_invalid_billing_currencies(currency):
    with pytest.raises(ValidationError) as ce:
        OrganizationBase(
            name="My Org",
            currency="EUR",
            billing_currency=currency,
            operations_external_id="EXT-ID",
        )
    errors = ce.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == ("billing_currency",)
    assert str(errors[0]["ctx"]["error"]) == f"Invalid iso4217 currency code: {currency}."
