from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import and_, exists
from sqlalchemy.sql.selectable import Select

from app.db.handlers import NotFoundError
from app.db.models import Account, AccountUser, User
from app.dependencies.auth import (
    CurrentAuthContext,
    authentication_required,
    check_operations_account,
)
from app.dependencies.db import (
    AccountRepository,
    AccountUserRepository,
    UserRepository,
)
from app.dependencies.path import AccountId, UserId
from app.enums import AccountStatus, AccountType, AccountUserStatus, UserStatus
from app.openapi import examples
from app.pagination import LimitOffsetPage, paginate
from app.rql import AccountRules, RQLQuery
from app.schemas.accounts import AccountCreate, AccountRead, AccountUpdate
from app.schemas.core import convert_model_to_schema, convert_schema_to_model
from app.schemas.users import UserRead

router = APIRouter()


async def persist_data_and_format_response(account_repo, data):
    """
    It persists the given data to the Account model and return back
    the Pydantic schema

    account_repo: an ORM model instance of AccountRepository
    data: the data to persist
    Return: AccountRead Pydantic Model
    """
    account = convert_schema_to_model(data, Account)
    db_account = await account_repo.create(account)
    return convert_model_to_schema(AccountRead, db_account)


async def update_data_and_format_response(
    id: str, account_repo: AccountRepository, data: AccountUpdate
):
    """
    It updates the given data to the Account model and return back
    the Pydantic schema

    account_repo: an ORM model instance of AccountRepository
    data: the data to update
    Return: AccountUpdate Pydantic Model
    """
    to_update = data.model_dump(exclude_none=True)
    if not to_update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field must be sent for update.",
        )
    db_account = await account_repo.update(id, data=to_update)
    return convert_model_to_schema(AccountRead, db_account)


def validate_required_conditions_before_update(account: Account):
    """
    This function performs the following required checks before
    proceeding to update an Account:
    1. Only Accounts classified as of type “Affiliate” can be updated.
    2. The account status cannot be DELETED

    A HTTPException with status 400 will be raised if at least one condition is not met.
    """
    if account.type != AccountType.AFFILIATE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot update an Account of type Operations.",
        )
    if account.status == AccountStatus.DELETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot update an Account Deleted.",
        )


async def validate_account_type_and_required_conditions(
    account_repo: AccountRepository, data: AccountCreate
):
    """
    This function performs the following required checks before
    proceeding to create an Account:
    1. Only Accounts classified as of type “Affiliate” can be created.
    2. The external_id field has to be unique and not in DELETED status.

    A HTTPException with status 400 will be raised if at least one condition is not met.
    """
    if data.type != AccountType.AFFILIATE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot create an Account of type Operations.",
        )
    if await account_repo.first(
        where_clauses=[
            Account.external_id == data.external_id,
            Account.status != AccountStatus.DELETED,
        ]
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An Account with external ID `{data.external_id}` already exists.",
        )


async def fetch_account_or_404(id: AccountId, account_repo: AccountRepository) -> Account:
    try:
        return await account_repo.get(id=id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    "",
    response_model=AccountRead,
    responses={
        201: {
            "description": "Account",
            "content": {
                "application/json": {
                    "example": examples.ACCOUNT_RESPONSE,
                }
            },
        },
    },
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_operations_account)],
)
async def create_account(
    data: Annotated[
        AccountCreate,
        Body(
            openapi_examples={
                "create_account": {
                    "summary": "Create Account.",
                    "description": ("Create a new affiliate Account."),
                    "value": {"name": "IBM", "external_id": "A-1234", "type": "affiliate"},
                }
            }
        ),
    ],
    account_repo: AccountRepository,
):
    """
    Creates an Account of type **Affiliate**.
    """
    await validate_account_type_and_required_conditions(account_repo, data)
    return await persist_data_and_format_response(account_repo, data)


@router.get(
    "/{id}",
    response_model=AccountRead,
    responses={
        200: {
            "description": "Account",
            "content": {"application/json": {"example": examples.ACCOUNT_RESPONSE}},
        },
    },
    dependencies=[Depends(check_operations_account)],
)
async def get_account_by_id(
    account: Annotated[Account, Depends(fetch_account_or_404)],
):
    return convert_model_to_schema(AccountRead, account)


@router.get(
    "",
    response_model=LimitOffsetPage[AccountRead],
    responses={
        200: {
            "description": "List of Accounts",
            "content": {
                "application/json": {
                    "example": {
                        "items": [examples.ACCOUNT_RESPONSE],
                        "total": 1,
                        "limit": 10,
                        "offset": 0,
                    },
                },
            },
        },
    },
    dependencies=[Depends(check_operations_account)],
)
async def get_accounts(
    account_repo: AccountRepository,
    base_query: Select = Depends(RQLQuery(AccountRules())),
):
    return await paginate(account_repo, AccountRead, base_query=base_query)


@router.put(
    "/{id}",
    response_model=AccountRead,
    responses={
        200: {
            "description": "Account",
            "content": {"application/json": {"example": examples.ACCOUNT_UPDATE_RESPONSE}},
        },
    },
    dependencies=[Depends(check_operations_account)],
)
async def update_account(
    data: Annotated[
        AccountUpdate,
        Body(
            openapi_examples={
                "update_account": {
                    "summary": "Update Account.",
                    "description": ("Update an existing affiliate Account."),
                    "value": {"name": "ibm", "external_id": "A-5678"},
                }
            }
        ),
    ],
    account_repo: AccountRepository,
    account: Annotated[Account, Depends(fetch_account_or_404)],
):
    """
    This Endpoint updates an Affiliate Account.

    The following conditions must be verified before proceeding with the operation of updating
    an account.
    1. The Account type must be OPERATIONS, otherwise a 403 error will be returned
    2. The Account status must be Active
    3. Only Accounts classified as of type “Affiliate” can be updated.
    4. Only the name and the external_id of the account can be modified.


    Raises:
        - HTTPException with status 403 if the check (1) fails
        - HTTPException with status 400 if the checks (2), (4) or (3) fail.
    """
    validate_required_conditions_before_update(account=account)
    return await update_data_and_format_response(
        id=account.id, account_repo=account_repo, data=data
    )


@router.get(
    "/{id}/users",
    response_model=LimitOffsetPage[UserRead],
    responses={
        200: {
            "description": "List of Users within the Account.",
            "content": {
                "application/json": {
                    "example": {
                        "items": [examples.USER_RESPONSE],
                        "total": 1,
                        "limit": 10,
                        "offset": 0,
                    },
                },
            },
        },
    },
    dependencies=[Depends(authentication_required)],
)
async def list_account_users(
    account: Annotated[Account, Depends(fetch_account_or_404)],
    auth_context: CurrentAuthContext,
    user_repo: UserRepository,
):
    """
    This Endpoint lists all the users bound to a given account id.
    The output is paginated by default.
    Raises:
        - HTTPException with status 404 if the given account is different from the context account
    Returns a list of accounts if any.
    """
    extra_conditions = []
    if auth_context.account.type == AccountType.AFFILIATE:  # type: ignore
        if auth_context.account != account:  # type: ignore
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account with ID `{account.id}` wasn't found.",
            )
        extra_conditions.extend(
            [
                exists().where(
                    and_(
                        AccountUser.account_id == account.id,
                        User.id == AccountUser.user_id,
                        AccountUser.status != AccountUserStatus.DELETED,
                    ),
                ),
                User.status != UserStatus.DELETED,
            ]
        )
    else:
        extra_conditions.append(
            exists().where(AccountUser.account_id == account.id, User.id == AccountUser.user_id)
        )

    # This runs a JOIN like
    # stmt = (
    #    select(User)
    #    .join(AccountUser, User.id == AccountUser.user_id)
    #    .where(AccountUser.account_id == account.id)
    # )

    return await paginate(
        user_repo,
        UserRead,
        where_clauses=extra_conditions,
    )


@router.delete(
    "/{id}/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(authentication_required)],
)
async def remove_user_from_account(
    account: Annotated[Account, Depends(fetch_account_or_404)],
    user_id: UserId,
    auth_context: CurrentAuthContext,
    accountuser_repo: AccountUserRepository,
):
    """
    This Endpoint removes a user from the giver account
    Raises:
        - HTTPException with status 404 if the given account is different from the context account
        - HTTPException 400 if the query doesn't return a valid account's user object

    """
    if auth_context.account.type == AccountType.AFFILIATE and auth_context.account != account:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID `{account.id}` wasn't found.",
        )
    account_user = await accountuser_repo.get_account_user(
        account_id=account.id,
        user_id=user_id,
        extra_conditions=[AccountUser.status != AccountUserStatus.DELETED],
    )
    if account_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The User `{user_id}` does not belong to the Account with ID `{account.id}`.",
        )
    await accountuser_repo.delete(id_or_obj=account_user)
