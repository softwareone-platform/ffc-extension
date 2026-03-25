import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.auth.context import AuthenticationContext
from app.db.handlers import (
    AccountUserHandler,
    CannotDeleteError,
    ConstraintViolationError,
    ModelHandler,
    NotFoundError,
)
from app.db.models import Account, AccountUser, Base, User
from app.enums import AccountStatus, AccountUserStatus, UserStatus
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
    operations_account: Account,
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
        user_id=user.id, account_id=operations_account.id, status=AccountStatus.ACTIVE
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
