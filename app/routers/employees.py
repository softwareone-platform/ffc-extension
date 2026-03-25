import secrets
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.api_clients.optscale import UserDoesNotExist
from app.dependencies.api_clients import APIModifierClient, OptscaleAuthClient, OptscaleClient
from app.dependencies.auth import check_operations_account
from app.schemas.employees import EmployeeCreate, EmployeeRead
from app.utils import wrap_http_error_in_502

router = APIRouter(dependencies=[Depends(check_operations_account)])


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
async def create_employee(
    data: Annotated[
        EmployeeCreate,
        Body(
            openapi_examples={
                "create_employee": {
                    "summary": "Create Employee.",
                    "description": ("Create a new FinOps for Cloud Employee."),
                    "value": {
                        "display_name": "Harry James Potter",
                        "email": "harry.potter@gryffindor.edu",
                    },
                }
            }
        ),
    ],
    api_modifier_client: APIModifierClient,
    optscale_client: OptscaleClient,
):
    with wrap_http_error_in_502("Error creating employee in FinOps for Cloud"):
        create_employee_response = await api_modifier_client.create_user(
            email=data.email,
            display_name=data.display_name,
            password=secrets.token_urlsafe(128),
        )

    with wrap_http_error_in_502("Error resetting the password for employee in FinOps for Cloud"):
        await optscale_client.reset_password(data.email)

        return EmployeeRead(**create_employee_response.json())


@router.get("/{email}", response_model=EmployeeRead)
async def get_employee_by_email(
    email: str,
    optscale_auth_client: OptscaleAuthClient,
):
    with wrap_http_error_in_502("Error checking employee existence in FinOps for Cloud"):
        try:
            response = await optscale_auth_client.get_existing_user_info(email)
        except UserDoesNotExist:
            raise HTTPException(
                status_code=404, detail=f"An employee with the email `{email}` wasn't found."
            )
        else:
            return EmployeeRead(**response.json()["user_info"])
