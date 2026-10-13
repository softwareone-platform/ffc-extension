from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import ColumnExpressionArgument, Select

from app.db.handlers import NotFoundError
from app.db.models import Account, Entitlement
from app.dependencies.api_clients import FFCAPIClient
from app.dependencies.auth import AuthorizedAccountTypes, CurrentAuthContext
from app.dependencies.db import (
    AccountRepository,
    EntitlementRepository,
)
from app.dependencies.path import EntitlementId
from app.enums import AccountStatus, AccountType, EntitlementStatus
from app.pagination import LimitOffsetPage, paginate
from app.rql import EntitlementRules, RQLQuery
from app.schemas.core import convert_model_to_schema, convert_schema_to_model
from app.schemas.entitlements import (
    EntitlementCreate,
    EntitlementRead,
)
from app.utils import wrap_http_error_in_502

# ============
# Dependencies
# ============


def common_extra_conditions(auth_ctx: CurrentAuthContext) -> list[ColumnExpressionArgument]:
    conditions: list[ColumnExpressionArgument] = []

    if auth_ctx.account.type == AccountType.AFFILIATE:  # type: ignore
        conditions.append(Entitlement.owner == auth_ctx.account)  # type: ignore
        conditions.append(Entitlement.status != EntitlementStatus.DELETED)

    return conditions


CommonConditions = Annotated[list[ColumnExpressionArgument], Depends(common_extra_conditions)]


async def fetch_entitlement_or_404(
    id: EntitlementId,
    entitlement_repo: EntitlementRepository,
    extra_conditions: CommonConditions,
) -> Entitlement:
    try:
        return await entitlement_repo.get(id=id, extra_conditions=extra_conditions)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


# ======
# Routes
# ======

router = APIRouter()


@router.get("", response_model=LimitOffsetPage[EntitlementRead])
async def get_entitlements(
    entitlement_repo: EntitlementRepository,
    extra_conditions: CommonConditions,
    base_query: Select = Depends(RQLQuery(EntitlementRules())),
):
    return await paginate(
        entitlement_repo, EntitlementRead, where_clauses=extra_conditions, base_query=base_query
    )


@router.post("", response_model=EntitlementRead, status_code=status.HTTP_201_CREATED)
async def create_entitlement(
    data: EntitlementCreate,
    account_repo: AccountRepository,
    entitlement_repo: EntitlementRepository,
    auth_context: CurrentAuthContext,
):
    owner = None
    if auth_context.account.type == AccountType.AFFILIATE:  # type: ignore
        if data.owner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Affiliate accounts cannot provide an owner for an Entitlement.",
            )
        owner = auth_context.account  # type: ignore
        if data.redeem_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Affiliate accounts cannot provide a redeem_at for an Entitlement.",
            )
    else:
        if not data.owner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin accounts must provide an owner for an Entitlement.",
            )
        try:
            owner = await account_repo.get(
                data.owner.id,
                [Account.status == AccountStatus.ACTIVE, Account.type == AccountType.AFFILIATE],
            )
        except NotFoundError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No Active Affiliate Account has been found with ID {data.owner.id}.",
            )

    existing_entitlement = await entitlement_repo.first(
        where_clauses=[
            Entitlement.datasource_id == data.datasource_id,
            Entitlement.owner_id == owner.id,
            Entitlement.status.in_([EntitlementStatus.NEW, EntitlementStatus.ACTIVE]),
        ]
    )
    if existing_entitlement:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"An Entitlement in status '{existing_entitlement.status.value}' "
                f"already exist for the data source {data.datasource_id}"
            ),
        )

    entitlement = convert_schema_to_model(data, Entitlement)
    entitlement.owner = owner
    db_entitlement = await entitlement_repo.create(entitlement)
    return convert_model_to_schema(EntitlementRead, db_entitlement)


@router.get("/{id}", response_model=EntitlementRead)
async def get_entitlement_by_id(
    entitlement: Annotated[Entitlement, Depends(fetch_entitlement_or_404)],
):
    return convert_model_to_schema(EntitlementRead, entitlement)


@router.post(
    "/{id}/terminate",
    response_model=EntitlementRead,
    dependencies=[Depends(AuthorizedAccountTypes(AccountType.ADMIN, AccountType.AFFILIATE))],
)
async def terminate_entitlement(
    entitlement: Annotated[Entitlement, Depends(fetch_entitlement_or_404)],
    entitlement_repo: EntitlementRepository,
    ffcapi_client: FFCAPIClient,
):
    if entitlement.status == EntitlementStatus.TERMINATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Entitlement is already terminated."
        )

    if entitlement.status != EntitlementStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Only active entitlements can be terminated,"
                f" current status is {entitlement.status.value}."
            ),
        )

    entitlement = await entitlement_repo.terminate(entitlement)
    with wrap_http_error_in_502("Error checking or creating user in FinOps for Cloud"):
        tag_data = None
        try:
            response = await ffcapi_client.get_tag_by_datasource_name(
                str(entitlement.linked_datasource_id),
                "entitlement",
            )
            tag_data = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                raise e

        if tag_data:
            await ffcapi_client.delete_tag(tag_data["id"])

    return convert_model_to_schema(EntitlementRead, entitlement)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entitlement_by_id(
    entitlement: Annotated[Entitlement, Depends(fetch_entitlement_or_404)],
    entitlement_repo: EntitlementRepository,
):
    if entitlement.status != EntitlementStatus.NEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Entitlements in status `new` can be deleted.",
        )
    await entitlement_repo.delete(entitlement)
