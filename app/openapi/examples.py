EVENTS = {
    "created": {
        "at": "2025-06-17T13:08:34.604204Z",
        "by": {"id": "FUSR-1234-5678", "type": "user", "name": "John Doe"},
    },
    "updated": {
        "at": "2025-07-04T11:00:00.171644Z",
        "by": {"id": "FUSR-1234-5678", "type": "user", "name": "John Doe"},
    },
}

ACCOUNT_RESPONSE = {
    "id": "FACC-5810-4583",
    "name": "IBM",
    "external_id": "A-1234",
    "type": "affiliate",
    "status": "active",
    "stats": {"entitlements": {"new": 0, "redeemed": 0, "terminated": 0}},
    "events": EVENTS,
}
ACCOUNT_UPDATE_RESPONSE = ACCOUNT_RESPONSE.copy()
ACCOUNT_UPDATE_RESPONSE["name"] = "ibm"


ORGANIZATION_RESPONSE = {
    "id": "FORG-7282-7898-3733",
    "linked_organization_id": "204a8397-ee26-4cf9-ac4b-1676d3f3acdd",
    "name": "Red Hat",
    "operations_external_id": "AGR-1234-5678-9012",
    "currency": "USD",
    "billing_currency": "EUR",
    "status": "active",
    "events": EVENTS,
}

ORGANIZATION_UPDATE_RESPONSE = ORGANIZATION_RESPONSE.copy()
ORGANIZATION_UPDATE_RESPONSE["name"] = "red hat"

SYSTEM_RESPONSE = {
    "id": "FTKN-9850-2106",
    "name": "IBM Extension",
    "external_id": "IBM_EXTENSION",
    "description": "IBM Cloud Extension",
    "owner": {
        "id": "FACC-5810-4583",
        "name": "IBM",
        "type": "affiliate",
    },
    "status": "active",
    "events": EVENTS,
}

SYSTEM_CREATE_RESPONSE = SYSTEM_RESPONSE.copy()
SYSTEM_CREATE_RESPONSE["jwt_secret"] = (  # nosec: B105
    "3e3068bfcacd587f75137afdead8f96adb016734a68630cac9e7a008"
    "458782a38ef61217d17406832f8fede61a7773866430f52084f8cac59311386e1b673261"
)

SYSTEM_UPDATE_RESPONSE = SYSTEM_RESPONSE.copy()
SYSTEM_UPDATE_RESPONSE["name"] = "ibm extension"
SYSTEM_UPDATE_RESPONSE["description"] = "ibm cloud extension"

SYSTEM_DISABLED_RESPONSE = SYSTEM_RESPONSE.copy()
SYSTEM_DISABLED_RESPONSE["status"] = "disabled"


USER_RESPONSE = {
    "name": "Fred Nerk",
    "email": "fred.nerk@example.com",
    "events": EVENTS,
    "id": "FUSR-9876-5431",
    "status": "active",
    "last_login_at": "2025-07-15T14:41:44.977941Z",
    "last_used_account": {"id": "FACC-5810-4583", "name": "IBM", "type": "affiliate"},
}

USER_UPDATE_RESPONSE = USER_RESPONSE.copy()
USER_UPDATE_RESPONSE["name"] = "fred nerk"

USER_DISABLED_RESPONSE = USER_RESPONSE.copy()
USER_DISABLED_RESPONSE["status"] = "disabled"

USER_INVITE_RESPONSE = {
    "name": "Fred Nerk",
    "email": "fred.nerk@example.com",
    "events": EVENTS,
    "id": "FUSR-9876-5431",
    "account_user": {
        "status": "invited",
        "events": EVENTS,
        "id": "FAUR-5715-6028-8678",
        "account": {"id": "FACC-5810-4583", "name": "IBM", "type": "affiliate"},
        "user": {
            "name": "Fred Nerk",
            "email": "fred.nerk@example.com",
            "id": "FUSR-9876-5431",
        },
        "invitation_token": (
            "ZV6dbu9NfxJpX8CebX3IW4dDjQ7ltqX8mZPIZnBWARLzMgOw0OgCSsQPqViZJRsCeATjOsjLtQPRwTCFj8ooTw",
        ),
        "invitation_token_expires_at": "2025-07-22T14:49:09.940621Z",
    },
    "status": "draft",
}
