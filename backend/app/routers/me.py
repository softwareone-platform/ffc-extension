from fastapi import APIRouter

from app.dependencies.auth import CurrentAuthContext
from app.openapi import examples
from app.schemas.accounts import AccountReference
from app.schemas.core import convert_model_to_schema
from app.schemas.me import Me
from app.schemas.systems import SystemReference
from app.schemas.users import UserReference

router = APIRouter()


@router.get(
    "",
    response_model=Me,
    responses={
        201: {
            "description": "Me",
            "content": {
                "application/json": {
                    "example": examples.ME_RESPONSE,
                }
            },
        },
    },
)
def me(
    auth_context: CurrentAuthContext,
):
    return Me(
        account=convert_model_to_schema(AccountReference, auth_context.account),
        system=convert_model_to_schema(SystemReference, auth_context.system)
        if auth_context.system
        else None,
        user=convert_model_to_schema(UserReference, auth_context.user)
        if auth_context.user
        else None,
    )
