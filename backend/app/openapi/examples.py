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

USER_RESPONSE = {
    "name": "Fred Nerk",
    "email": "fred.nerk@example.com",
    "events": EVENTS,
    "id": "FUSR-9876-5431",
    "status": "active",
}
