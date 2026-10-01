from typing import Any

import pytest

from app.db.models import Account
from app.enums import AccountType
from app.events.subscriptions.utils import get_datasource_id, is_product_supported


def account(products: str | None) -> Account:
    """An affiliate account that is not persisted: only `products` is read."""
    return Account(
        id="ACC-1234-5678", name="Microsoft", type=AccountType.AFFILIATE, products=products
    )


def subscription(product_id: str, vendor: str | None = "ds-0001-0001") -> dict[str, Any]:
    payload: dict[str, Any] = {"id": "SUB-1234-5678", "product": {"id": product_id}}
    if vendor is not None:
        payload["externalIds"] = {"vendor": vendor}
    return payload


# -- get_datasource_id --


def test_get_datasource_id_returns_the_vendor_external_id() -> None:
    """The datasource id is the subscription's vendor external id."""
    assert get_datasource_id(subscription("PRD-1111-1111")) == "ds-0001-0001"


@pytest.mark.parametrize(
    "payload",
    [
        {"id": "SUB-1234-5678"},
        {"id": "SUB-1234-5678", "externalIds": {}},
        {"id": "SUB-1234-5678", "externalIds": {"client": "CLI-1"}},
    ],
)
def test_get_datasource_id_returns_none_without_a_vendor_id(payload: dict[str, Any]) -> None:
    """A subscription carrying no vendor external id has no datasource."""
    assert get_datasource_id(payload) is None


# -- is_product_supported --


@pytest.mark.parametrize(
    ("products", "product_id"),
    [
        ("PRD-1111-1111", "PRD-1111-1111"),
        ("PRD-1111-1111,PRD-2222-2222", "PRD-2222-2222"),
        ("PRD-1111-1111, PRD-2222-2222", "PRD-2222-2222"),
        ("prd-1111-1111", "PRD-1111-1111"),
        ("PRD-1111-1111", "prd-1111-1111"),
    ],
)
def test_is_product_supported_accepts_a_product_the_account_sells(
    products: str, product_id: str
) -> None:
    """Membership ignores case and the whitespace around the comma separated ids."""
    assert is_product_supported(subscription(product_id), account(products)) is True


@pytest.mark.parametrize("products", [None, "", " , ", "PRD-2222-2222", "PRD-1111-11"])
def test_is_product_supported_rejects_anything_else(products: str | None) -> None:
    """An empty, unset or non matching product list supports nothing."""
    assert is_product_supported(subscription("PRD-1111-1111"), account(products)) is False
