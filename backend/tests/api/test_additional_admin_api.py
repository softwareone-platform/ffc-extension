import pytest
from httpx import AsyncClient

from app.db.models import Organization, System, User
from app.enums import ActivityStatus, OrganizationStatus
from tests.types import ActivityLogFetcher, AddAdminMocker, ModelFactory

LINKED_ORG_ID = "1bf8f888-d88b-8d88-8e8f-88fefa8f888"
EMAIL = "peter.parker@spiderman.com"
REQUEST = {"email": EMAIL, "display_name": "Peter Parker", "notes": "What a wonderful idea"}


# The notes of the steps, formatted by `step_notes`.
USER_CREATED = "FinOps for Cloud user {user} ({email}) created."
USER_EXISTS = "FinOps for Cloud user {user} ({email}) already exists."
EMPLOYEE_ADDED = "User {user} added as employee of FinOps for Cloud organization {org}."
EMPLOYEE_EXISTS = "User {user} is already an employee of FinOps for Cloud organization {org}."
MADE_ADMIN = "User {user} made admin of FinOps for Cloud organization {org}."
RESET_SENT = "Password reset email sent to {email}."


def step_notes(user_id: str, *templates: str) -> list[str]:
    return [template.format(user=user_id, email=EMAIL, org=LINKED_ORG_ID) for template in templates]


def operation_key(organization: Organization) -> str:
    return f"add-admin:{organization.id}:{EMAIL}"


def in_progress_message() -> str:
    return f"Adding 'Peter Parker' ({EMAIL}) as admin of 'ACME CO'."


def completed_message(organization: Organization) -> str:
    return (
        f"'Peter Parker' ({EMAIL}) added as admin of 'ACME CO' ({organization.id}). "
        "Reason: What a wonderful idea"
    )


# ---------------------------------------------------------------------------
# Successful requests
# ---------------------------------------------------------------------------


async def test_add_admin_answers_no_content(
    admin_client: AsyncClient,
    add_admin_organization: Organization,
    add_admin_mocker: AddAdminMocker,
) -> None:
    """A successful request answers 204 with no body."""
    add_admin_mocker(add_admin_organization, employee_status=409)

    response = await admin_client.post(
        f"/organizations/{add_admin_organization.id}/add-admin", json=REQUEST
    )

    assert response.status_code == 204
    assert response.content == b""


async def test_add_existing_user_as_admin_records_a_completed_entry(
    admin_client: AsyncClient,
    add_admin_organization: Organization,
    ffc_extension: System,
    add_admin_mocker: AddAdminMocker,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """Adding an existing user leaves one completed entry by the caller, with the reason and
    a note for each step."""
    user_id = add_admin_mocker(add_admin_organization, employee_status=409)

    await admin_client.post(f"/organizations/{add_admin_organization.id}/add-admin", json=REQUEST)

    (entry,) = await fetch_operation_entries(operation_key(add_admin_organization))
    assert entry.action == "organization.admin_added"
    assert entry.status == ActivityStatus.COMPLETED
    assert entry.message == completed_message(add_admin_organization)
    assert entry.recorded_by_id == ffc_extension.id
    assert entry.changes == []
    assert [note.message for note in entry.notes] == [
        *step_notes(user_id, USER_EXISTS, EMPLOYEE_EXISTS, MADE_ADMIN),
        "Completed.",
    ]


async def test_add_new_user_as_admin_notes_every_step(
    admin_client: AsyncClient,
    add_admin_organization: Organization,
    add_admin_mocker: AddAdminMocker,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """A new user gets a note for its creation, the employee, the admin role and the
    password reset email."""
    user_id = add_admin_mocker(add_admin_organization, user_exists=False)

    response = await admin_client.post(
        f"/organizations/{add_admin_organization.id}/add-admin", json=REQUEST
    )

    assert response.status_code == 204
    (entry,) = await fetch_operation_entries(operation_key(add_admin_organization))
    assert entry.status == ActivityStatus.COMPLETED
    assert entry.changes == []
    assert [note.message for note in entry.notes] == [
        *step_notes(user_id, USER_CREATED, EMPLOYEE_ADDED, MADE_ADMIN, RESET_SENT),
        "Completed.",
    ]


async def test_add_admin_keys_the_operation_by_the_lower_cased_email(
    admin_client: AsyncClient,
    add_admin_organization: Organization,
    add_admin_mocker: AddAdminMocker,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """The operation key holds the email lower-cased, so its case does not split the entries."""
    add_admin_mocker(add_admin_organization, email="Peter.Parker@SpiderMan.com")

    await admin_client.post(
        f"/organizations/{add_admin_organization.id}/add-admin",
        json={**REQUEST, "email": "Peter.Parker@SpiderMan.com"},
    )

    (entry,) = await fetch_operation_entries(operation_key(add_admin_organization))
    assert entry.status == ActivityStatus.COMPLETED


async def test_add_admin_again_after_completion_records_a_new_entry(
    admin_client: AsyncClient,
    add_admin_organization: Organization,
    add_admin_mocker: AddAdminMocker,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """Adding the same admin again once the first entry is completed starts a new entry."""
    add_admin_mocker(add_admin_organization)
    add_admin_mocker(add_admin_organization, employee_status=409)

    for _ in range(2):
        response = await admin_client.post(
            f"/organizations/{add_admin_organization.id}/add-admin", json=REQUEST
        )
        assert response.status_code == 204

    entries = await fetch_operation_entries(operation_key(add_admin_organization))
    assert [entry.status for entry in entries] == [ActivityStatus.COMPLETED] * 2
    assert entries[0].id != entries[1].id


# ---------------------------------------------------------------------------
# Failed requests: the entry and its notes survive the rollback of the request
# ---------------------------------------------------------------------------


EMPLOYEE_ERROR = (
    "Error Adding Employee Peter Parker to FinOps for Cloud Organization ACME CO.: 403 - Error."
)
ADMIN_ROLE_ERROR = (
    "Error Promoting User Peter Parker to Admin in FinOps for Cloud ACME CO.: 403 - Error."
)


@pytest.mark.transactional_db
@pytest.mark.parametrize(
    ("failure", "done", "detail"),
    [
        (
            {"user_exists": False, "create_user_status": 403},
            [],
            "Error checking or creating user in FinOps for Cloud: 403 - Error.",
        ),
        ({"employee_status": 403}, [USER_EXISTS], EMPLOYEE_ERROR),
        ({"user_exists": False, "employee_status": 403}, [USER_CREATED], EMPLOYEE_ERROR),
        ({"admin_role_status": 403}, [USER_EXISTS, EMPLOYEE_ADDED], ADMIN_ROLE_ERROR),
        (
            {"user_exists": False, "reset_password_status": 403},
            [USER_CREATED, EMPLOYEE_ADDED, MADE_ADMIN],
            "Error resetting the password for employee in FinOps for Cloud: 403 - Error.",
        ),
    ],
    ids=["create-user", "employee", "employee-of-new-user", "admin-role", "reset-password"],
)
async def test_failed_add_admin_leaves_an_in_progress_entry_naming_the_failed_step(
    admin_client: AsyncClient,
    add_admin_organization: Organization,
    add_admin_mocker: AddAdminMocker,
    fetch_operation_entries: ActivityLogFetcher,
    failure: dict[str, int | bool],
    done: list[str],
    detail: str,
) -> None:
    """A request failing in FinOps for Cloud answers 502 and leaves the entry in progress,
    with the notes of the steps done and a failure note naming the failed step."""
    user_id = add_admin_mocker(add_admin_organization, **failure)

    response = await admin_client.post(
        f"/organizations/{add_admin_organization.id}/add-admin", json=REQUEST
    )

    assert response.status_code == 502
    assert response.json()["detail"] == detail
    (entry,) = await fetch_operation_entries(operation_key(add_admin_organization))
    assert entry.action == "organization.admin_added"
    assert entry.status == ActivityStatus.IN_PROGRESS
    assert entry.message == in_progress_message()
    assert [note.message for note in entry.notes] == [
        *step_notes(user_id, *done),
        f"Attempt failed: {detail}",
    ]


@pytest.mark.transactional_db
async def test_repeated_add_admin_completes_the_entry_of_the_failed_request(
    admin_client: AsyncClient,
    add_admin_organization: Organization,
    ffc_extension: System,
    admin_user: User,
    admin_user_token: str,
    add_admin_mocker: AddAdminMocker,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """Another admin repeating a failed request completes the same entry, which becomes
    theirs; the notes keep the actor of each attempt."""
    user_id = add_admin_mocker(add_admin_organization, user_exists=False, admin_role_status=403)
    add_admin_mocker(add_admin_organization, employee_status=409)

    failed = await admin_client.post(
        f"/organizations/{add_admin_organization.id}/add-admin", json=REQUEST
    )
    repeated = await admin_client.post(
        f"/organizations/{add_admin_organization.id}/add-admin",
        json=REQUEST,
        headers={"Authorization": f"Bearer {admin_user_token}"},
    )

    assert (failed.status_code, repeated.status_code) == (502, 204)
    (entry,) = await fetch_operation_entries(operation_key(add_admin_organization))
    assert entry.status == ActivityStatus.COMPLETED
    assert entry.message == completed_message(add_admin_organization)
    assert entry.recorded_by_id == admin_user.id
    first_notes = step_notes(user_id, USER_CREATED, EMPLOYEE_ADDED)
    repeated_notes = step_notes(user_id, USER_EXISTS, EMPLOYEE_EXISTS, MADE_ADMIN)
    assert [(note.message, note.recorded_by_id) for note in entry.notes] == [
        *((message, ffc_extension.id) for message in first_notes),
        (f"Attempt failed: {ADMIN_ROLE_ERROR}", ffc_extension.id),
        *((message, admin_user.id) for message in repeated_notes),
        ("Completed.", admin_user.id),
    ]


# ---------------------------------------------------------------------------
# Rejected requests
# ---------------------------------------------------------------------------


async def test_cannot_add_admin_to_a_deleted_organization(
    admin_client: AsyncClient,
    organization_factory: ModelFactory[Organization],
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """A deleted organization is answered with 400, and nothing is recorded."""
    organization = await organization_factory(
        name="ACME CO",
        currency="EUR",
        linked_organization_id=LINKED_ORG_ID,
        status=OrganizationStatus.DELETED,
    )

    response = await admin_client.post(f"/organizations/{organization.id}/add-admin", json=REQUEST)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Cannot add administrator: organization ACME CO is deleted."
    )
    assert await fetch_operation_entries(operation_key(organization)) == []


async def test_cannot_add_admin_with_an_affiliate_account(
    affiliate_client: AsyncClient, organization_factory: ModelFactory[Organization]
) -> None:
    """Only admin accounts can add an admin: affiliates get 403."""
    organization = await organization_factory(operations_external_id="EXTERNAL_ID_2")

    response = await affiliate_client.post(
        f"/organizations/{organization.id}/add-admin", json=REQUEST
    )

    assert response.status_code == 403


async def test_cannot_add_admin_to_an_unknown_organization(admin_client: AsyncClient) -> None:
    """An unknown organization is answered with 404."""
    response = await admin_client.post("/organizations/FORG-6636-4936-8593/add-admin", json=REQUEST)

    assert response.status_code == 404
