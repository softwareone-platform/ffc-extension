from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.constants import JWT_ALGORITHM, JWT_LEEWAY, UNAUTHORIZED_EXCEPTION
from app.conf import Settings
from app.db.handlers import (
    AccountHandler,
    AccountUserHandler,
    DatabaseError,
    UserHandler,
)
from app.db.models import Account, AccountUser, User
from app.enums import AccountStatus, AccountUserStatus, UserStatus
from app.hasher import pbkdf2_sha256
from app.schemas.accounts import AccountReference
from app.schemas.auth import Login, LoginRead, RefreshAccessToken
from app.schemas.core import convert_model_to_schema
from app.schemas.users import UserReference


def generate_access_and_refresh_tokens(settings: Settings, subject: str, account_id: str):
    now = datetime.now(UTC)
    default_claims = {
        "sub": subject,
        "iat": now,
        "nbf": now,
    }
    access_claims = {
        **default_claims,
        "account_id": account_id,
        "exp": now + timedelta(minutes=settings.auth_access_jwt_lifespan_minutes),
    }
    refresh_claims = {
        **default_claims,
        "exp": now + timedelta(days=settings.auth_refresh_jwt_lifespan_days),
    }
    access_token = jwt.encode(
        access_claims,
        settings.auth_access_jwt_secret,
        algorithm=JWT_ALGORITHM,
    )
    refresh_token = jwt.encode(
        refresh_claims,
        settings.auth_refresh_jwt_secret,
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


async def get_tokens_from_refresh(
    settings: Settings, db_session: AsyncSession, refresh_token_data: RefreshAccessToken
) -> LoginRead:
    user_handler = UserHandler(db_session)
    account_user_handler = AccountUserHandler(db_session)
    account_handler = AccountHandler(db_session)
    try:
        claims = jwt.decode(
            refresh_token_data.refresh_token,
            settings.auth_refresh_jwt_secret,
            options={"require": ["exp", "nbf", "iat", "sub"]},
            algorithms=[JWT_ALGORITHM],
            leeway=JWT_LEEWAY,
        )
        user_id = claims["sub"]
        user = await user_handler.get(
            user_id,
            extra_conditions=[User.status == UserStatus.ACTIVE],
        )
        account_id = refresh_token_data.account.id
        account = await account_handler.get(
            account_id,
            extra_conditions=[Account.status == AccountStatus.ACTIVE],
        )
        account_user = await account_user_handler.get_account_user(
            account_id=account_id,
            user_id=user_id,
            extra_conditions=[AccountUser.status == AccountUserStatus.ACTIVE],
        )
        if not account_user:
            raise UNAUTHORIZED_EXCEPTION

        await user_handler.update(user.id, {"last_used_account_id": account_id})
        tokens = generate_access_and_refresh_tokens(settings, user_id, account_id)

        return LoginRead(
            user=convert_model_to_schema(UserReference, user),
            account=convert_model_to_schema(AccountReference, account),
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
        )

    except (jwt.InvalidTokenError, DatabaseError) as e:
        raise UNAUTHORIZED_EXCEPTION from e


async def get_tokens_from_credentials(
    settings: Settings, db_session: AsyncSession, login_data: Login
) -> LoginRead:
    user_handler = UserHandler(db_session)
    account_user_handler = AccountUserHandler(db_session)
    account_handler = AccountHandler(db_session)
    try:
        user = await user_handler.first(
            where_clauses=[
                User.status == UserStatus.ACTIVE,
                func.lower(User.email) == login_data.email.lower(),
            ]
        )
        if not user:
            raise UNAUTHORIZED_EXCEPTION
        if not pbkdf2_sha256.verify(login_data.password.get_secret_value(), user.password):  # type: ignore
            raise UNAUTHORIZED_EXCEPTION

        account_id: str = (
            user.last_used_account_id if not login_data.account else login_data.account.id  # type: ignore
        )
        account = await account_handler.get(
            account_id,
            extra_conditions=[Account.status == AccountStatus.ACTIVE],
        )
        account_user = await account_user_handler.get_account_user(
            account_id=account_id,
            user_id=user.id,
            extra_conditions=[AccountUser.status == AccountUserStatus.ACTIVE],
        )
        if not account_user:
            raise UNAUTHORIZED_EXCEPTION
        await user_handler.update(
            user.id,
            {
                "last_login_at": datetime.now(UTC),
                "last_used_account_id": account_id,
            },
        )
        tokens = generate_access_and_refresh_tokens(settings, user.id, account_id)
        return LoginRead(
            user=convert_model_to_schema(UserReference, user),
            account=convert_model_to_schema(AccountReference, account),
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
        )

    except DatabaseError as e:
        raise UNAUTHORIZED_EXCEPTION from e
