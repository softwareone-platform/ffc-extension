import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException, status
from pytest_capsqlalchemy import SQLAlchemyCapturer
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import (
    JWTBearer,
    JWTCredentials,
)
from app.auth.context import AuthenticationContext, auth_context
from app.conf import Settings
from app.db.models import System, User
from app.dependencies.auth import (
    authentication_required,
    check_operations_account,
    get_authentication_context,
)
from app.enums import AccountType, AccountUserStatus, ActorType, SystemStatus, UserStatus
from tests.types import JWTTokenFactory, ModelFactory


async def test_jwt_bearer(mocker: MockerFixture, jwt_token_factory: JWTTokenFactory):
    bearer = JWTBearer()
    request = mocker.Mock()
    token = jwt_token_factory(
        "test",
        "secretsecretsecretsecretsecretsecretsecretsecret",
    )
    request.headers = {"Authorization": f"Bearer {token}"}
    credentials = await bearer(request)
    assert credentials is not None
    assert isinstance(credentials, JWTCredentials)
    assert credentials.claim["sub"] == "test"


async def test_jwt_bearer_invalid_token(mocker: MockerFixture):
    bearer = JWTBearer()
    request = mocker.Mock()
    request.headers = {"Authorization": "Bearer 1234567890"}
    with pytest.raises(HTTPException) as exc_info:
        await bearer(request)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized."


async def test_jwt_bearer_no_token(mocker: MockerFixture):
    bearer = JWTBearer()
    request = mocker.Mock()
    request.headers = {}
    credentials = await bearer(request)
    assert credentials is None


async def test_get_authentication_context_system(
    mocker: MockerFixture,
    gcp_jwt_token: str,
    gcp_extension: System,
    db_session: AsyncSession,
    test_settings: Settings,
    capsqlalchemy: SQLAlchemyCapturer,
):
    bearer = JWTBearer()
    request = mocker.Mock()
    request.headers = {"Authorization": f"Bearer {gcp_jwt_token}"}
    credentials = await bearer(request)
    assert credentials is not None

    with pytest.raises(LookupError):
        auth_context.get()

    with capsqlalchemy:
        async with asynccontextmanager(get_authentication_context)(
            test_settings, db_session, credentials
        ) as context:
            assert isinstance(context, AuthenticationContext)
            assert context.actor_type == ActorType.SYSTEM
            assert context.system == gcp_extension
            assert context.user is None
            assert context.account == gcp_extension.owner
            assert context.get_actor() == gcp_extension
            assert auth_context.get() == context

        capsqlalchemy.assert_query_count(1)

    with pytest.raises(LookupError):
        auth_context.get()


@pytest.mark.parametrize(
    "system_status",
    [SystemStatus.DELETED, SystemStatus.DISABLED],
)
async def test_get_authentication_context_system_not_active(
    mocker: MockerFixture,
    system_factory: ModelFactory[System],
    jwt_token_factory: JWTTokenFactory,
    db_session: AsyncSession,
    system_status: SystemStatus,
    test_settings: Settings,
):
    system = await system_factory(
        status=system_status,
        jwt_secret="secretsecretsecretsecretsecretsecretsecretsecretsecretsecret",
    )
    jwt_token = jwt_token_factory(
        system.id,
        "secretsecretsecretsecretsecretsecretsecretsecretsecretsecret",
    )
    bearer = JWTBearer()
    request = mocker.Mock()
    request.headers = {"Authorization": f"Bearer {jwt_token}"}
    credentials = await bearer(request)
    assert credentials is not None

    with pytest.raises(HTTPException) as exc_info:
        async with asynccontextmanager(get_authentication_context)(
            test_settings, db_session, credentials
        ):
            pass

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized."

    with pytest.raises(LookupError):
        auth_context.get()


async def test_get_authentication_context_system_jwt_lifespan_exceeded(
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
    system_factory: ModelFactory[System],
    jwt_token_factory: JWTTokenFactory,
    db_session: AsyncSession,
    test_settings: Settings,
):
    system = await system_factory(
        jwt_secret="secretsecretsecretsecretsecretsecretsecretsecretsecretsecret",
    )
    jwt_token = jwt_token_factory(
        system.id,
        "secretsecretsecretsecretsecretsecretsecretsecretsecretsecret",
        nbf=datetime.now(UTC),
        exp=(
            datetime.now(UTC)
            + timedelta(
                minutes=test_settings.system_jwt_token_max_lifespan_minutes,
                seconds=1,
            )
        ),
    )
    bearer = JWTBearer()
    request = mocker.Mock()
    request.headers = {"Authorization": f"Bearer {jwt_token}"}
    credentials = await bearer(request)
    assert credentials is not None

    with caplog.at_level(level=logging.INFO):
        with pytest.raises(HTTPException) as exc_info:
            async with asynccontextmanager(get_authentication_context)(
                test_settings, db_session, credentials
            ):
                pass
    assert "system jwt token cannot be valid for more than 5 minutes." in caplog.text

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized."

    with pytest.raises(LookupError):
        auth_context.get()


async def test_get_authentication_context_user(
    mocker: MockerFixture,
    user_factory: ModelFactory[User],
    jwt_token_factory: JWTTokenFactory,
    db_session: AsyncSession,
    test_settings: Settings,
    capsqlalchemy: SQLAlchemyCapturer,
):
    user = await user_factory()
    jwt_token = jwt_token_factory(user.id, test_settings.auth_access_jwt_secret)
    bearer = JWTBearer()
    request = mocker.Mock()
    request.headers = {"Authorization": f"Bearer {jwt_token}"}
    credentials = await bearer(request)
    assert credentials is not None

    with pytest.raises(LookupError):
        auth_context.get()

    with capsqlalchemy:
        async with asynccontextmanager(get_authentication_context)(
            test_settings, db_session, credentials
        ) as context:
            assert isinstance(context, AuthenticationContext)
            assert context.actor_type == ActorType.USER
            assert context.system is None
            assert context.user == user
            assert context.account == user.last_used_account
            assert context.get_actor() == user
            assert auth_context.get() == context

        capsqlalchemy.assert_query_count(3)

    with pytest.raises(LookupError):
        auth_context.get()


@pytest.mark.parametrize(
    "user_status",
    [UserStatus.DELETED, UserStatus.DISABLED, UserStatus.DRAFT],
)
async def test_get_authentication_context_user_invalid_status(
    mocker: MockerFixture,
    user_factory: ModelFactory[User],
    jwt_token_factory: JWTTokenFactory,
    db_session: AsyncSession,
    user_status: UserStatus,
    test_settings: Settings,
):
    user = await user_factory(status=user_status)
    jwt_token = jwt_token_factory(user.id, test_settings.auth_access_jwt_secret)

    bearer = JWTBearer()
    request = mocker.Mock()
    request.headers = {"Authorization": f"Bearer {jwt_token}"}
    credentials = await bearer(request)
    assert credentials is not None

    with pytest.raises(HTTPException) as exc_info:
        async with asynccontextmanager(get_authentication_context)(
            test_settings, db_session, credentials
        ):
            pass

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized."

    with pytest.raises(LookupError):
        auth_context.get()


@pytest.mark.parametrize(
    "accountuser_status",
    [
        AccountUserStatus.DELETED,
        AccountUserStatus.INVITATION_EXPIRED,
        AccountUserStatus.INVITED,
    ],
)
async def test_get_authentication_context_user_invalid_accountuser_status(
    mocker: MockerFixture,
    user_factory: ModelFactory[User],
    jwt_token_factory: JWTTokenFactory,
    db_session: AsyncSession,
    accountuser_status: AccountUserStatus,
    test_settings: Settings,
):
    user = await user_factory(accountuser_status=accountuser_status)
    jwt_token = jwt_token_factory(user.id, test_settings.auth_access_jwt_secret)

    bearer = JWTBearer()
    request = mocker.Mock()
    request.headers = {"Authorization": f"Bearer {jwt_token}"}
    credentials = await bearer(request)
    assert credentials is not None

    with pytest.raises(HTTPException) as exc_info:
        async with asynccontextmanager(get_authentication_context)(
            test_settings, db_session, credentials
        ):
            pass

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized."

    with pytest.raises(LookupError):
        auth_context.get()


async def test_get_authentication_context_user_account_does_not_exist(
    mocker: MockerFixture,
    user_factory: ModelFactory[User],
    jwt_token_factory: JWTTokenFactory,
    db_session: AsyncSession,
    test_settings: Settings,
):
    user = await user_factory()
    jwt_token = jwt_token_factory(
        user.id, test_settings.auth_access_jwt_secret, account_id="FACC-0000-0000"
    )

    bearer = JWTBearer()
    request = mocker.Mock()
    request.headers = {"Authorization": f"Bearer {jwt_token}"}
    credentials = await bearer(request)
    assert credentials is not None

    with pytest.raises(HTTPException) as exc_info:
        async with asynccontextmanager(get_authentication_context)(
            test_settings, db_session, credentials
        ):
            pass

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Unauthorized."

    with pytest.raises(LookupError):
        auth_context.get()


def test_check_operations_account_error(
    mocker: MockerFixture,
):
    context = mocker.Mock()
    context.account.type = (AccountType.AFFILIATE,)
    with pytest.raises(HTTPException) as exc_info:
        check_operations_account(context)
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "You've found the door, but you don't have the key." in str(exc_info.value.detail)


def test_check_operations_account_ok(
    mocker: MockerFixture,
):
    context = mocker.Mock()
    context.account.type = AccountType.OPERATIONS
    check_operations_account(context)


def test_check_operations_account_no_auth_context():
    with pytest.raises(HTTPException) as exc_info:
        check_operations_account(None)

    assert exc_info.value.status_code == 401


async def test_authentication_required(
    mocker: MockerFixture,
    gcp_jwt_token: str,
    gcp_extension: System,
    db_session: AsyncSession,
    test_settings: Settings,
    capsqlalchemy: SQLAlchemyCapturer,
):
    bearer = JWTBearer()
    request = mocker.Mock()
    request.headers = {"Authorization": f"Bearer {gcp_jwt_token}"}
    credentials = await bearer(request)
    assert credentials is not None

    with pytest.raises(LookupError):
        auth_context.get()

    with capsqlalchemy:
        async with asynccontextmanager(authentication_required)(
            test_settings, db_session, credentials
        ):
            assert auth_context.get() is not None

        capsqlalchemy.assert_query_count(1)

    with pytest.raises(LookupError):
        auth_context.get()


async def test_authentication_required_not_authenticated(
    mocker: MockerFixture,
    db_session: AsyncSession,
    test_settings: Settings,
):
    bearer = JWTBearer()
    request = mocker.Mock()
    request.headers = {}
    credentials = await bearer(request)
    assert credentials is None

    with pytest.raises(LookupError):
        auth_context.get()

    with pytest.raises(HTTPException) as exc_info:
        async with asynccontextmanager(authentication_required)(
            test_settings, db_session, credentials
        ):
            pass
    assert exc_info.value.status_code == 401

    with pytest.raises(LookupError):
        auth_context.get()
