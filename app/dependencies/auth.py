import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_clients.mpt import MPTClient
from app.auth.auth import MPTAuthContext
from app.auth.constants import UNAUTHORIZED_EXCEPTION
from app.auth.context import AuthenticationContext, auth_context
from app.db import handlers, models
from app.dependencies.api_clients import InstallationClient
from app.dependencies.core import AppSettings
from app.dependencies.db import DBSession

logger = logging.getLogger(__name__)


class MaxLifespanExceededError(Exception):
    pass


async def get_authentication_context(
    settings: AppSettings,
    db_session: DBSession,
    mpt_auth_context: MPTAuthContext,
    mpt_installation_client: InstallationClient,
):
    """
    This function gets the authentication context from a JWT bearer token.
    It manages System and User actors and return the related authentication context.
    If no  credentials are provided, it returns a default unauthenticated context.

    """
    if mpt_auth_context:
        account_id = mpt_auth_context.account_id
        actor_id = mpt_auth_context.user_id or mpt_auth_context.token_id
        if not actor_id:
            raise UNAUTHORIZED_EXCEPTION
        try:
            if actor_id.startswith(models.System.MPT_PREFIX):
                pass
                context = await get_authentication_context_for_system(
                    mpt_installation_client=mpt_installation_client,
                    db_session=db_session,
                    account_id=account_id,
                    system_id=actor_id,
                )
            else:
                context = await get_authentication_context_for_account_user(
                    mpt_installation_client=mpt_installation_client,
                    db_session=db_session,
                    account_id=account_id,
                    user_id=actor_id,
                )
        except (jwt.InvalidTokenError, handlers.DatabaseError, MaxLifespanExceededError) as e:
            logger.info(f"Authentication error: {e}")
            raise UNAUTHORIZED_EXCEPTION from e

        reset_token = auth_context.set(context)

        try:
            yield context
            return
        finally:
            auth_context.reset(reset_token)
    yield


async def get_authentication_context_for_account_user(
    mpt_installation_client: MPTClient,
    db_session: AsyncSession,
    account_id: str,
    user_id: str,
) -> AuthenticationContext:
    """
    This functions retrieves the authentication context from a specific account user
    identified by a JWT bearer token.
    """

    user_handler = handlers.UserHandler(db_session)
    account_user_handler = handlers.AccountUserHandler(db_session)
    account_handler = handlers.AccountHandler(db_session)
    account = await account_handler.first(
        where_clauses=[
            models.Account.external_id == account_id,
            models.Account.status == models.AccountStatus.ACTIVE,
        ],
    )
    if not account:
        raise UNAUTHORIZED_EXCEPTION
    user = await user_handler.first(
        where_clauses=[
            models.User.external_id == user_id,
            models.User.status == models.UserStatus.ACTIVE,
        ],
    )
    if not user:
        user_data = await mpt_installation_client.get_user(user_id)
        user = await user_handler.create(
            models.User(
                name=user_data["name"],
                email=user_data["email"],
                external_id=user_id,
                status=models.UserStatus.ACTIVE,
            )
        )

    account_user = await account_user_handler.get_account_user(
        account_id=account_id,
        user_id=user_id,
        extra_conditions=[models.AccountUser.status == models.AccountUserStatus.ACTIVE],
    )
    if not account_user:
        account_user = await account_user_handler.create(
            models.AccountUser(
                account=account,
                user=user,
                status=models.AccountUserStatus.ACTIVE,
            )
        )

    context = AuthenticationContext(
        account=account,
        actor_type=models.ActorType.USER,
        user=user,
    )
    return context


async def get_authentication_context_for_system(
    mpt_installation_client: MPTClient,
    db_session: AsyncSession,
    account_id: str,
    system_id: str,
) -> AuthenticationContext:
    """
    This functions retrieves the authentication context from a specific system account
    identified by a JWT bearer token.
    """
    system_handler = handlers.SystemHandler(db_session)
    account_handler = handlers.AccountHandler(db_session)
    account = await account_handler.first(
        where_clauses=[
            models.Account.external_id == account_id,
            models.Account.status == models.AccountStatus.ACTIVE,
        ],
    )
    if not account:
        raise UNAUTHORIZED_EXCEPTION
    system = await system_handler.first(
        where_clauses=[
            models.System.external_id == system_id,
            models.System.status == models.SystemStatus.ACTIVE,
        ],
    )
    if not system:
        token_data = await mpt_installation_client.get_token(system_id)
        system = await system_handler.create(
            models.System(
                name=token_data["name"],
                external_id=system_id,
                owner=account,
                status=models.SystemStatus.ACTIVE,
            )
        )

    context = AuthenticationContext(
        account=account,
        actor_type=models.ActorType.SYSTEM,
        system=system,
    )
    return context


async def authentication_required(
    settings: AppSettings,
    db_session: DBSession,
    mpt_auth_context: MPTAuthContext,
    mpt_installation_client: InstallationClient,
) -> AsyncGenerator[None]:
    async with asynccontextmanager(get_authentication_context)(
        settings, db_session, mpt_auth_context, mpt_installation_client
    ) as auth_context:
        if not auth_context:
            raise UNAUTHORIZED_EXCEPTION
        yield


def check_operations_account(
    context: Annotated[AuthenticationContext | None, Depends(get_authentication_context)],
) -> None:
    """
    This function ensures that the account type is of type OPERATIONS
    """
    if not context:
        raise UNAUTHORIZED_EXCEPTION

    if context.account.type != models.AccountType.OPERATIONS:
        # This API can only be consumed in the context of an Operations Account
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You've found the door, but you don't have the key.",
        )
    return None


CurrentAuthContext = Annotated[AuthenticationContext | None, Depends(get_authentication_context)]
