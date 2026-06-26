import contextlib
import secrets

import jwt
import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_auth_context, resolve_installation
from app.auth.context import AuthenticationContext, MPTAuthContext, auth_context
from app.conf import Settings
from app.db.models import Account, System
from app.dependencies.auth import (
    AuthorizedAccountTypes,
    authentication_required,
    get_authentication_context,
    get_authentication_context_for_account_user,
    get_authentication_context_for_system,
)
from app.enums import AccountStatus, AccountType, ActorType, SystemStatus
from tests.types import ModelFactory

ACCOUNT_ID_CLAIM = "https://claims.softwareone.com/accountId"
ACCOUNT_TYPE_CLAIM = "https://claims.softwareone.com/accountType"
INSTALLATION_CLAIM = "https://claims.softwareone.com/installationId"
USER_CLAIM = "https://claims.softwareone.com/userId"
TOKEN_CLAIM = "https://claims.softwareone.com/apiTokenId"


def _credentials(**claims: object) -> HTTPAuthorizationCredentials:
    """Wrap the given claim set in a Bearer credentials object (helper for auth tests)."""
    token = jwt.encode(claims, secrets.token_hex(16), algorithm="HS256")
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


# ---------------------------------------------------------------------------
# app.auth.context.AuthenticationContext.get_actor
# ---------------------------------------------------------------------------


async def test_get_actor_returns_system_for_system_context(
    account_factory: ModelFactory[Account],
    system_factory: ModelFactory[System],
) -> None:
    """`AuthenticationContext.get_actor` returns the system when the actor type is SYSTEM."""
    account = await account_factory()
    system = await system_factory(owner=account)
    ctx = AuthenticationContext(account=account, actor_type=ActorType.SYSTEM, system=system)
    assert ctx.get_actor() == system


async def test_get_actor_returns_user_for_user_context(
    account_factory: ModelFactory[Account],
    user_factory: ModelFactory,
) -> None:
    """`AuthenticationContext.get_actor` returns the user when the actor type is not SYSTEM."""
    account = await account_factory()
    user = await user_factory(account=account)
    ctx = AuthenticationContext(account=account, actor_type=ActorType.USER, user=user)
    assert ctx.get_actor() == user


# ---------------------------------------------------------------------------
# app.auth.auth.resolve_installation
# ---------------------------------------------------------------------------


async def test_resolve_installation_returns_first_installation_id(httpx_mock: HTTPXMock) -> None:
    """`resolve_installation` returns the id of the first installation in the response."""
    httpx_mock.add_response(json={"data": [{"id": "EXI-1"}, {"id": "EXI-2"}]})
    assert await resolve_installation("ACC-1") == "EXI-1"


async def test_resolve_installation_returns_none_when_no_installations(
    httpx_mock: HTTPXMock,
) -> None:
    """`resolve_installation` returns None when the account has no installations."""
    httpx_mock.add_response(json={"data": []})
    assert await resolve_installation("ACC-1") is None


# ---------------------------------------------------------------------------
# app.auth.auth.get_auth_context
# ---------------------------------------------------------------------------


async def test_get_auth_context_raises_without_credentials() -> None:
    """`get_auth_context` raises a 401 when no credentials are supplied."""
    with pytest.raises(HTTPException) as exc_info:
        await get_auth_context(None)  # type: ignore[arg-type]
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_auth_context_reads_context_from_claims() -> None:
    """`get_auth_context` builds an `MPTAuthContext` from the token claims without an HTTP call."""
    credentials = _credentials(
        **{
            ACCOUNT_ID_CLAIM: "ACC-1",
            ACCOUNT_TYPE_CLAIM: "Operations",
            INSTALLATION_CLAIM: "EXI-1",
            USER_CLAIM: "USR-1",
            TOKEN_CLAIM: None,
        }
    )
    ctx = await get_auth_context(credentials)
    assert ctx.account_id == "ACC-1"
    assert ctx.account_type == "Operations"
    assert ctx.installation_id == "EXI-1"
    assert ctx.user_id == "USR-1"


async def test_get_auth_context_resolves_installation_when_missing(httpx_mock: HTTPXMock) -> None:
    """`get_auth_context` resolves the installation id when the claim is absent."""
    httpx_mock.add_response(json={"data": [{"id": "EXI-RESOLVED"}]})
    credentials = _credentials(
        **{
            ACCOUNT_ID_CLAIM: "ACC-1",
            ACCOUNT_TYPE_CLAIM: "Operations",
            USER_CLAIM: "USR-1",
        }
    )
    ctx = await get_auth_context(credentials)
    assert ctx.installation_id == "EXI-RESOLVED"


# ---------------------------------------------------------------------------
# app.dependencies.auth.get_authentication_context_for_account_user
# ---------------------------------------------------------------------------


async def test_account_user_context_raises_when_account_missing(
    db_session: AsyncSession, mocker: MockerFixture
) -> None:
    """`get_authentication_context_for_account_user` raises 401 for an unknown account."""
    with pytest.raises(HTTPException) as exc_info:
        await get_authentication_context_for_account_user(
            mocker.Mock(), db_session, "ACC-MISSING", "USR-1"
        )
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


async def test_account_user_context_creates_user_from_mpt(
    db_session: AsyncSession,
    account_factory: ModelFactory[Account],
    mocker: MockerFixture,
) -> None:
    """An unknown user is fetched from MPT and persisted with an active account link."""
    account = await account_factory(status=AccountStatus.ACTIVE, external_id="ACC-NEWUSER")
    client = mocker.Mock()
    client.get_user = mocker.AsyncMock(return_value={"name": "Jane", "email": "jane@example.com"})

    ctx = await get_authentication_context_for_account_user(
        client, db_session, "ACC-NEWUSER", "USR-NEW"
    )

    assert ctx.actor_type == ActorType.USER
    assert ctx.user is not None
    assert ctx.user.email == "jane@example.com"
    assert ctx.account == account
    client.get_user.assert_awaited_once_with("USR-NEW")


async def test_account_user_context_uses_existing_user(
    db_session: AsyncSession,
    account_factory: ModelFactory[Account],
    user_factory: ModelFactory,
    mocker: MockerFixture,
) -> None:
    """An already-known active user is reused without fetching from MPT."""
    account = await account_factory(status=AccountStatus.ACTIVE, external_id="ACC-HASUSER")
    user = await user_factory(external_id="USR-EXIST", account=account)
    client = mocker.Mock()

    ctx = await get_authentication_context_for_account_user(
        client, db_session, "ACC-HASUSER", "USR-EXIST"
    )

    assert ctx.user == user
    client.get_user.assert_not_called()


# ---------------------------------------------------------------------------
# app.dependencies.auth.get_authentication_context_for_system
# ---------------------------------------------------------------------------


async def test_system_context_raises_when_account_missing(
    db_session: AsyncSession, mocker: MockerFixture
) -> None:
    """`get_authentication_context_for_system` raises 401 for an unknown account."""
    with pytest.raises(HTTPException) as exc_info:
        await get_authentication_context_for_system(
            mocker.Mock(), db_session, "ACC-MISSING", "TKN-1"
        )
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


async def test_system_context_creates_system_from_mpt(
    db_session: AsyncSession,
    account_factory: ModelFactory[Account],
    mocker: MockerFixture,
) -> None:
    """An unknown system token is fetched from MPT and persisted under the account."""
    account = await account_factory(status=AccountStatus.ACTIVE, external_id="ACC-NEWSYS")
    client = mocker.Mock()
    client.get_token = mocker.AsyncMock(return_value={"name": "robot"})

    ctx = await get_authentication_context_for_system(client, db_session, "ACC-NEWSYS", "TKN-NEW")

    assert ctx.actor_type == ActorType.SYSTEM
    assert ctx.account == account
    assert ctx.system is not None
    assert ctx.system.name == "robot"
    client.get_token.assert_awaited_once_with("TKN-NEW")


async def test_system_context_returns_existing_system(
    db_session: AsyncSession,
    account_factory: ModelFactory[Account],
    system_factory: ModelFactory[System],
    mocker: MockerFixture,
) -> None:
    """An already-known active system is returned without calling MPT."""
    account = await account_factory(status=AccountStatus.ACTIVE, external_id="ACC-EXIST")
    system = await system_factory(
        external_id="TKN-EXIST", owner=account, status=SystemStatus.ACTIVE
    )
    client = mocker.Mock()

    ctx = await get_authentication_context_for_system(client, db_session, "ACC-EXIST", "TKN-EXIST")

    assert ctx.system == system
    client.get_token.assert_not_called()


# ---------------------------------------------------------------------------
# app.dependencies.auth.get_authentication_context (async generator)
# ---------------------------------------------------------------------------


async def test_get_authentication_context_requires_an_actor_id(
    db_session: AsyncSession, test_settings: Settings, mocker: MockerFixture
) -> None:
    """The context generator raises 401 when the auth context has neither user nor token id."""
    mpt_ctx = MPTAuthContext(account_id="ACC-1", account_type="Operations")
    with pytest.raises(HTTPException) as exc_info:
        async with contextlib.asynccontextmanager(get_authentication_context)(
            test_settings, db_session, mpt_ctx, mocker.Mock()
        ):
            pass
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_authentication_context_yields_none_without_mpt_context(
    db_session: AsyncSession, test_settings: Settings, mocker: MockerFixture
) -> None:
    """The context generator yields None when there is no MPT auth context (anonymous)."""
    async with contextlib.asynccontextmanager(get_authentication_context)(
        test_settings,
        db_session,
        None,  # type: ignore[arg-type]
        mocker.Mock(),  # type: ignore[arg-type]
    ) as ctx:
        assert ctx is None


async def test_get_authentication_context_translates_database_error(
    db_session: AsyncSession,
    test_settings: Settings,
    account_factory: ModelFactory[Account],
    mocker: MockerFixture,
) -> None:
    """A database error while resolving the actor is translated into a 401."""
    await account_factory(status=AccountStatus.ACTIVE, external_id="ACC-DBERR")
    mpt_ctx = MPTAuthContext(account_id="ACC-DBERR", account_type="Operations", user_id="USR-ERR")
    client = mocker.Mock()
    # A null name violates the NOT NULL constraint, raising a handlers.DatabaseError on create.
    client.get_user = mocker.AsyncMock(return_value={"name": None, "email": None})

    with pytest.raises(HTTPException) as exc_info:
        async with contextlib.asynccontextmanager(get_authentication_context)(
            test_settings, db_session, mpt_ctx, client
        ):
            pass
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_authentication_context_sets_and_resets_context_var(
    db_session: AsyncSession,
    test_settings: Settings,
    account_factory: ModelFactory[Account],
    system_factory: ModelFactory[System],
    mocker: MockerFixture,
) -> None:
    """The generator sets `auth_context` while active and resets it on exit."""
    account = await account_factory(status=AccountStatus.ACTIVE, external_id="ACC-CTXVAR")
    system = await system_factory(
        external_id="TKN-CTXVAR", owner=account, status=SystemStatus.ACTIVE
    )
    mpt_ctx = MPTAuthContext(
        account_id="ACC-CTXVAR", account_type="Operations", token_id="TKN-CTXVAR"
    )

    with pytest.raises(LookupError):
        auth_context.get()

    async with contextlib.asynccontextmanager(get_authentication_context)(
        test_settings, db_session, mpt_ctx, mocker.Mock()
    ) as ctx:
        assert ctx.system == system
        assert auth_context.get() is ctx

    with pytest.raises(LookupError):
        auth_context.get()


# ---------------------------------------------------------------------------
# app.dependencies.auth.authentication_required
# ---------------------------------------------------------------------------


async def test_authentication_required_allows_authenticated_request(
    db_session: AsyncSession,
    test_settings: Settings,
    account_factory: ModelFactory[Account],
    system_factory: ModelFactory[System],
    mocker: MockerFixture,
) -> None:
    """`authentication_required` yields control for an authenticated actor."""
    account = await account_factory(status=AccountStatus.ACTIVE, external_id="ACC-REQ")
    await system_factory(external_id="TKN-REQ", owner=account, status=SystemStatus.ACTIVE)
    mpt_ctx = MPTAuthContext(account_id="ACC-REQ", account_type="Operations", token_id="TKN-REQ")

    entered = False
    async with contextlib.asynccontextmanager(authentication_required)(
        test_settings, db_session, mpt_ctx, mocker.Mock()
    ):
        entered = True
    assert entered is True


async def test_authentication_required_rejects_anonymous_request(
    db_session: AsyncSession, test_settings: Settings, mocker: MockerFixture
) -> None:
    """`authentication_required` raises 401 when there is no authentication context."""
    with pytest.raises(HTTPException) as exc_info:
        async with contextlib.asynccontextmanager(authentication_required)(
            test_settings,
            db_session,
            None,  # type: ignore[arg-type]
            mocker.Mock(),  # type: ignore[arg-type]
        ):
            pass
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# app.dependencies.auth.AuthorizedAccountTypes
# ---------------------------------------------------------------------------


def test_authorized_account_types_rejects_missing_context() -> None:
    """`AuthorizedAccountTypes` raises 401 when no authentication context is present."""
    checker = AuthorizedAccountTypes(AccountType.OPERATIONS)
    with pytest.raises(HTTPException) as exc_info:
        checker(None)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


async def test_authorized_account_types_forbids_disallowed_type(
    account_factory: ModelFactory[Account],
) -> None:
    """`AuthorizedAccountTypes` raises 403 when the account type is not allowed."""
    account = await account_factory(type=AccountType.AFFILIATE)
    checker = AuthorizedAccountTypes(AccountType.OPERATIONS)
    with pytest.raises(HTTPException, match="you don't have the key") as exc_info:
        checker(AuthenticationContext(account=account))
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


async def test_authorized_account_types_allows_permitted_type(
    account_factory: ModelFactory[Account],
) -> None:
    """`AuthorizedAccountTypes` permits a request whose account type is allowed."""
    account = await account_factory(type=AccountType.OPERATIONS)
    checker = AuthorizedAccountTypes(AccountType.OPERATIONS)
    # Returns control (no HTTPException) for an allowed account type.
    checker(AuthenticationContext(account=account))
