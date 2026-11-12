from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.context import AuthenticationContext, auth_context
from app.db.handlers import ClientAccountHandler, OrganizationHandler
from app.db.models import Account, Organization
from tests.db.models import ChildForTests, ParentWithChildrenForTests
from tests.types import ModelFactory


@pytest.fixture
def organization_handler(db_session: AsyncSession) -> OrganizationHandler:
    """An `OrganizationHandler` bound to the test session."""
    return OrganizationHandler(db_session)


@pytest.fixture
def client_account_handler(db_session: AsyncSession) -> ClientAccountHandler:
    """A `ClientAccountHandler` bound to the test session."""
    return ClientAccountHandler(db_session)


@pytest.fixture
def sensitive_column() -> Generator[str]:
    """Flag `Organization.operations_external_id` as sensitive for one test; yield its key."""
    column = Organization.__table__.c.operations_external_id
    column.info["sensitive"] = True
    yield "operations_external_id"
    column.info.pop("sensitive", None)


@pytest.fixture
def sql_statements() -> Generator[list[str]]:
    """Collect the SQL statements sent to the database while the test runs."""
    statements: list[str] = []

    def _collect(*args: Any) -> None:
        statements.append(args[2])  # (conn, cursor, statement, parameters, context, executemany)

    event.listen(Engine, "before_cursor_execute", _collect)
    yield statements
    event.remove(Engine, "before_cursor_execute", _collect)


@pytest.fixture
def parent_factory(db_session: AsyncSession) -> ModelFactory[ParentWithChildrenForTests]:
    """Persist a `ParentWithChildrenForTests` with its (empty) children collection loaded."""

    async def _parent(name: str = "Parent") -> ParentWithChildrenForTests:
        parent = ParentWithChildrenForTests(name=name)
        db_session.add(parent)
        await db_session.flush()
        await db_session.refresh(parent, attribute_names=["children"])
        return parent

    return _parent


@pytest.fixture
def child_factory(db_session: AsyncSession) -> ModelFactory[ChildForTests]:
    """Persist a `ChildForTests`, by default without a parent."""

    async def _child(name: str = "Child", parent_id: str | None = None) -> ChildForTests:
        child = ChildForTests(name=name, parent_id=parent_id)
        db_session.add(child)
        await db_session.flush()
        return child

    return _child


@pytest.fixture
async def actorless_auth_context(
    admin_account: Account,
) -> AsyncGenerator[AuthenticationContext]:
    """An authentication context with an account but no actor, for the duration of the test."""
    context = AuthenticationContext(account=admin_account)
    token = auth_context.set(context)
    yield context
    auth_context.reset(token)


@pytest.fixture
def opted_out_model(mocker: MockerFixture) -> type[ChildForTests]:
    """`ChildForTests` with `__activity_log__ = False` for one test."""
    mocker.patch.object(ChildForTests, "__activity_log__", False, create=True)
    return ChildForTests
