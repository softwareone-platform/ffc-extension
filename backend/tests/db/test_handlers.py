from datetime import UTC, datetime

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.auth.context import AuthenticationContext
from app.db.handlers import (
    AccountUserHandler,
    CannotDeleteError,
    ClientAccountHandler,
    ConstraintViolationError,
    ModelHandler,
    NotFoundError,
    TerminationFeedbackHandler,
)
from app.db.models import Account, AccountUser, Base, ClientAccount, Organization, System, User
from app.enums import AccountStatus, AccountUserStatus, TerminationReason, UserStatus
from tests.db.models import (
    DeletableAuditModelForTests,
    DeletableModelForTests,
    DeletableModelStatus,
    ModelForTests,
    NonDeletableModelWithEnumStatusForTests,
    ParentModelForTests,
)
from tests.types import ModelFactory


class ModelForTestsHandler(ModelHandler[ModelForTests]):
    pass


class ParentModelForTestsHandler(ModelHandler[ParentModelForTests]):
    pass


class DeletableModelForTestsHandler(ModelHandler[DeletableModelForTests]):
    pass


class DeletableAuditModelForTestsHandler(ModelHandler[DeletableAuditModelForTests]):
    pass


class NonDeletableModelWithEnumStatusForTestsHandler(
    ModelHandler[NonDeletableModelWithEnumStatusForTests]
):
    pass


async def test_create_success(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)
    test_obj = ModelForTests(name="Test Object")

    created_obj = await handler.create(test_obj)

    assert created_obj.id is not None
    assert created_obj.id.startswith(ModelForTests.PK_PREFIX)
    assert created_obj.name == "Test Object"


async def test_create_constraint_violation(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)
    obj1 = ModelForTests(name="Duplicate Name")
    await handler.create(obj1)

    obj2 = ModelForTests(name="Duplicate Name")

    with pytest.raises(ConstraintViolationError):
        await handler.create(obj2)


async def test_get_success(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)
    test_obj = ModelForTests(name="Get Test Object")
    await handler.create(test_obj)

    fetched_obj = await handler.get(test_obj.id)
    assert fetched_obj.id == test_obj.id
    assert fetched_obj.name == "Get Test Object"


async def test_get_not_found(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)

    with pytest.raises(NotFoundError):
        await handler.get("not-found")


async def test_update_success(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)
    test_obj = ModelForTests(name="Update Test Object")
    created_obj = await handler.create(test_obj)

    updated_obj = await handler.update(created_obj.id, {"name": "Updated Name"})
    assert updated_obj.name == "Updated Name"


async def test_fetch_page(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)

    # Create multiple objects
    for i in range(5):
        await handler.create(ModelForTests(name=f"Object {i}"))

    results = await handler.query_db(limit=3, offset=1)
    assert len(results) == 3


async def test_count(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)
    for i in range(5):
        await handler.create(ModelForTests(name=f"Object {i}"))
    count = await handler.count()
    assert count == 5


async def test_first(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)
    for i in range(5):
        await handler.create(ModelForTests(name=f"Object {i}"))
    first_result = await handler.first(where_clauses=[ModelForTests.name.like("Object%")])

    assert first_result is not None
    assert first_result.name.startswith("Object")


async def test_fetch_page_extra_conditions(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)
    test_obj1 = ModelForTests(name="Condition Test 1", status="inactive")
    test_obj2 = ModelForTests(name="Condition Test 2", status="active")

    await handler.create(test_obj1)
    await handler.create(test_obj2)

    # Fetch with extra condition to only get active status
    results = await handler.query_db(where_clauses=[ModelForTests.status == "active"])
    assert len(results) == 1
    assert results[0].name == "Condition Test 2"


async def test_get_extra_conditions(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)
    test_obj1 = ModelForTests(name="Condition Test 1", status="inactive")
    test_obj2 = ModelForTests(name="Condition Test 2", status="active")

    await handler.create(test_obj1)
    await handler.create(test_obj2)

    # Fetch with extra condition to only get active status
    result = await handler.get(test_obj2.id, extra_conditions=[ModelForTests.status == "active"])
    assert result == test_obj2


async def test_get_default_options_with_joinedload(db_session: AsyncSession):
    parent_obj = ParentModelForTests(description="Parent Description")
    db_session.add(parent_obj)
    await db_session.commit()
    handler = ModelForTestsHandler(db_session)
    handler.default_options = [joinedload(ModelForTests.parent)]
    test_obj = ModelForTests(name="With Related")
    test_obj.parent = parent_obj
    await handler.create(test_obj)
    db_session.expunge_all()

    fetched_obj = await handler.get(test_obj.id)
    assert fetched_obj.parent.description == "Parent Description"


async def test_count_with_extra_conditions(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)

    await handler.create(ModelForTests(name="Object 1", status="inactive"))
    await handler.create(ModelForTests(name="Object 2", status="active"))

    count_active = await handler.count(where_clauses=[ModelForTests.status == "active"])
    assert count_active == 1


async def test_filter_with_default_load_options(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)
    parent = ParentModelForTests(description="Parent Description")
    db_session.add(parent)
    await db_session.commit()
    await db_session.refresh(parent)

    model = ModelForTests(name="Test Object", parent=parent)
    await handler.create(model)

    handler.default_options = [joinedload(ModelForTests.parent)]
    results = await handler.query_db(where_clauses=[ModelForTests.name == "Test Object"])
    assert len(results) == 1
    assert results[0].parent.description == "Parent Description"


async def test_first_with_default_load_options(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)
    parent = ParentModelForTests(description="First Parent Description")
    db_session.add(parent)
    await db_session.commit()
    await db_session.refresh(parent)

    model = ModelForTests(name="First Test Object", parent=parent)
    await handler.create(model)

    handler.default_options = [joinedload(ModelForTests.parent)]
    first_result = await handler.first(where_clauses=[ModelForTests.name == "First Test Object"])
    assert first_result is not None
    assert first_result.parent.description == "First Parent Description"


async def test_get_or_create_with_default_load_options(db_session: AsyncSession):
    handler = ModelForTestsHandler(db_session)
    parent = ParentModelForTests(description="GetOrCreate Parent")
    db_session.add(parent)
    await db_session.commit()
    await db_session.refresh(parent)

    handler.default_options = [joinedload(ModelForTests.parent)]

    obj, created = await handler.get_or_create(
        defaults={"parent_id": parent.id}, name="GetOrCreate Object"
    )
    assert created is True
    assert obj.parent.description == "GetOrCreate Parent"

    # Ensure fetching without creation
    obj, created = await handler.get_or_create(
        defaults={"parent_id": parent.id}, name="GetOrCreate Object"
    )
    assert created is False
    assert obj.parent.description == "GetOrCreate Parent"


async def test_update_or_create_creates_missing_object(db_session: AsyncSession) -> None:
    """`update_or_create` creates an object from filters and defaults when none matches."""
    handler = ModelForTestsHandler(db_session)

    obj, created = await handler.update_or_create(
        defaults={"status": "inactive"}, name="UpdateOrCreate Object"
    )

    assert created is True
    assert obj.id.startswith(ModelForTests.PK_PREFIX)
    assert obj.name == "UpdateOrCreate Object"
    assert obj.status == "inactive"


async def test_update_or_create_updates_existing_object(db_session: AsyncSession) -> None:
    """`update_or_create` applies defaults to the object matching the filters."""
    handler = ModelForTestsHandler(db_session)
    existing = await handler.create(ModelForTests(name="UpdateOrCreate Object"))

    obj, created = await handler.update_or_create(
        defaults={"status": "inactive"}, name="UpdateOrCreate Object"
    )

    assert created is False
    assert obj.id == existing.id
    assert obj.status == "inactive"
    assert await handler.count() == 1


async def test_update_or_create_applies_extra_conditions(db_session: AsyncSession) -> None:
    """`update_or_create` ignores objects that don't satisfy `extra_conditions`."""
    handler = ModelForTestsHandler(db_session)
    parent = ParentModelForTests(description="Parent")
    db_session.add(parent)
    await db_session.commit()
    existing = await handler.create(
        ModelForTests(name="Inactive Object", status="inactive", parent_id=parent.id)
    )

    obj, created = await handler.update_or_create(
        defaults={"name": "Active Object"},
        extra_conditions=[ModelForTests.status == "active"],
        parent_id=parent.id,
    )

    assert created is True
    assert obj.id != existing.id
    assert obj.name == "Active Object"


@pytest.mark.parametrize(
    ("model_cls", "handler_cls", "initial_status", "exception"),
    [
        pytest.param(
            DeletableModelForTests,
            DeletableModelForTestsHandler,
            DeletableModelStatus.ACTIVE,
            None,
            id="deletable_delete_active",
        ),
        pytest.param(
            DeletableModelForTests,
            DeletableModelForTestsHandler,
            DeletableModelStatus.DELETED,
            CannotDeleteError("DeletableModelForTests object is already deleted"),
            id="deletable_delete_deleted_fail",
        ),
        pytest.param(
            DeletableAuditModelForTests,
            DeletableAuditModelForTestsHandler,
            DeletableModelStatus.ACTIVE,
            None,
            id="deletable_audit_delete_active",
        ),
        pytest.param(
            ModelForTests,
            ModelForTestsHandler,
            "active",
            CannotDeleteError("ModelForTests status column is not an Enum"),
            id="non_enum_status_delete_fail",
        ),
        pytest.param(
            ParentModelForTests,
            ParentModelForTestsHandler,
            None,
            CannotDeleteError("ParentModelForTests does not have a status column"),
            id="no_status_delete_fail",
        ),
        pytest.param(
            NonDeletableModelWithEnumStatusForTests,
            NonDeletableModelWithEnumStatusForTestsHandler,
            "active",
            CannotDeleteError(
                "NonDeletableModelWithEnumStatusForTests "
                "status column does not have a 'deleted' value"
            ),
            id="status_enum_no_delete_state_fail",
        ),
    ],
)
async def test_delete(
    db_session: AsyncSession,
    model_cls: type[Base],
    handler_cls: type[ModelHandler],
    initial_status: DeletableModelStatus,
    exception: Exception | None,
):
    handler = handler_cls(db_session)
    model_fields = {"name": "Delete Test Object"}

    if initial_status is not None:
        model_fields["status"] = initial_status

    test_obj = model_cls(**model_fields)
    await handler.create(test_obj)

    if exception is None:
        await handler.delete(test_obj)
        await db_session.refresh(test_obj)
        assert test_obj.status == DeletableModelStatus.DELETED  # type: ignore[attr-defined]
    else:
        with pytest.raises(exception.__class__, match=str(exception)):
            await handler.delete(test_obj)


async def test_deleted_by_user_id(
    db_session: AsyncSession,
    admin_account: Account,
    accountuser_factory: ModelFactory[AccountUser],
    user_factory: ModelFactory[User],
    mocker: MockerFixture,
):
    user = await user_factory(
        name="Peter Parker",
        email="peter.parker@spiderman.com",
        status=UserStatus.ACTIVE,
    )
    user_actor = await user_factory()
    account_user = await accountuser_factory(
        user_id=user.id, account_id=admin_account.id, status=AccountStatus.ACTIVE
    )

    db_session.add(account_user)
    await db_session.commit()
    mock_actor = mocker.AsyncMock()
    mock_actor.id = account_user.id
    handler = AccountUserHandler(db_session)
    mock_actor = mocker.AsyncMock()
    mock_actor.id = user_actor.id
    mock_auth_context = mocker.AsyncMock(spec=AuthenticationContext)
    mock_auth_context.get_actor.return_value = mock_actor
    mock_context_var = mocker.MagicMock()
    mock_context_var.get.return_value = mock_auth_context

    mocker.patch("app.db.handlers.auth_context", mock_context_var)

    await handler.delete_by_user(user_id=user.id)
    result = await db_session.get(AccountUser, account_user.id)
    assert result is not None
    assert result.status == AccountUserStatus.DELETED
    assert result.deleted_at is not None
    assert result.deleted_by_id == user_actor.id


async def test_termination_feedback_upsert_for_organization_creates(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
) -> None:
    """A feedback is created when the organization doesn't have one yet."""
    organization = await organization_factory()
    handler = TerminationFeedbackHandler(db_session)

    feedback = await handler.upsert_for_organization(
        organization,
        reason=TerminationReason.OTHER,
        comments="We are moving to another tool.",
    )

    assert feedback.id.startswith("FFBK-")
    assert feedback.organization_id == organization.id
    assert feedback.reason == TerminationReason.OTHER
    assert feedback.comments == "We are moving to another tool."


async def test_termination_feedback_upsert_for_organization_replaces_existing(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
) -> None:
    """An existing feedback gets the new reason and comments instead of creating a new one."""
    organization = await organization_factory()
    handler = TerminationFeedbackHandler(db_session)
    existing = await handler.upsert_for_organization(
        organization, reason=TerminationReason.TOO_COMPLEX, comments="Too many screens."
    )

    feedback = await handler.upsert_for_organization(organization, reason=TerminationReason.OTHER)

    assert feedback.id == existing.id
    assert feedback.reason == TerminationReason.OTHER
    assert feedback.comments is None
    assert await handler.count() == 1


async def test_client_account_update_or_create_creates_with_actor(
    db_session: AsyncSession, ffc_extension_auth_context: AuthenticationContext
) -> None:
    """A new `ClientAccount` is created with `created_by`/`updated_by` set to the current actor."""
    handler = ClientAccountHandler(db_session)

    client_account, created = await handler.update_or_create(
        defaults={"name": "Client", "icon": "/icons/client.png"},
        external_id="ACC-1234-5678",
    )

    assert created is True
    assert client_account.id.startswith(ClientAccount.PK_PREFIX)
    assert client_account.external_id == "ACC-1234-5678"
    assert client_account.name == "Client"
    assert client_account.icon == "/icons/client.png"
    assert client_account.created_by == ffc_extension_auth_context.system
    assert client_account.updated_by == ffc_extension_auth_context.system


async def test_client_account_update_or_create_updates_existing(
    db_session: AsyncSession,
    client_account_factory: ModelFactory[ClientAccount],
    gcp_extension: System,
    ffc_extension_auth_context: AuthenticationContext,
) -> None:
    """An existing `ClientAccount` is updated in place, keeping its creator."""
    existing = await client_account_factory(
        name="Old Name",
        external_id="ACC-1234-5678",
        created_by=gcp_extension,
        updated_by=gcp_extension,
    )
    handler = ClientAccountHandler(db_session)

    client_account, created = await handler.update_or_create(
        defaults={"name": "New Name"}, external_id="ACC-1234-5678"
    )

    assert created is False
    assert client_account.id == existing.id
    assert client_account.name == "New Name"
    assert client_account.created_by == gcp_extension
    assert client_account.updated_by == ffc_extension_auth_context.system
    assert await handler.count() == 1


async def test_client_account_update_or_create_skips_unchanged(
    db_session: AsyncSession,
    client_account_factory: ModelFactory[ClientAccount],
    gcp_extension: System,
    ffc_extension_auth_context: AuthenticationContext,
) -> None:
    """Calling `update_or_create` with unchanged values doesn't touch the `ClientAccount`."""
    existing = await client_account_factory(
        name="Client",
        external_id="ACC-1234-5678",
        created_by=gcp_extension,
        updated_by=gcp_extension,
    )
    handler = ClientAccountHandler(db_session)

    client_account, created = await handler.update_or_create(
        defaults={"name": "Client"}, external_id="ACC-1234-5678"
    )

    assert created is False
    assert client_account.updated_by == gcp_extension
    assert client_account.updated_at == existing.updated_at


async def test_client_account_update_or_create_ignores_soft_deleted(
    db_session: AsyncSession,
    client_account_factory: ModelFactory[ClientAccount],
    ffc_extension_auth_context: AuthenticationContext,
) -> None:
    """A soft-deleted `ClientAccount` is left untouched and a new one is created instead."""
    deleted = await client_account_factory(
        name="Old Name", external_id="ACC-1234-5678", deleted_at=datetime.now(UTC)
    )
    handler = ClientAccountHandler(db_session)

    client_account, created = await handler.update_or_create(
        defaults={"name": "New Name"}, external_id="ACC-1234-5678"
    )

    assert created is True
    assert client_account.id != deleted.id
    assert client_account.name == "New Name"
    await db_session.refresh(deleted)
    assert deleted.name == "Old Name"


async def test_client_account_external_id_unique_for_non_deleted(
    client_account_factory: ModelFactory[ClientAccount],
) -> None:
    """Two non-deleted `ClientAccount`s can't share the same `external_id`."""
    await client_account_factory(external_id="ACC-1234-5678")

    with pytest.raises(IntegrityError, match="ix_client_accounts_external_id_for_non_deleted"):
        await client_account_factory(external_id="ACC-1234-5678")
