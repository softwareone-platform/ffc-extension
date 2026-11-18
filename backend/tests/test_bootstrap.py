import json
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from app.bootstrap import bootstrap, get_affiliate_products
from app.conf import Settings
from app.db.models import Account
from app.enums import AccountStatus, AccountType
from tests.types import ModelFactory

EXTERNAL_ID = "testextid"


def test_bootstrap_requests_new_identity_and_saves_it(
    tmp_path: Path,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
) -> None:
    """`bootstrap` requests a fresh identity when no identity file exists and saves the result."""
    ziti = mocker.patch("app.bootstrap.ziticorn")
    mocker.patch("app.bootstrap.get_instance_external_id", return_value=EXTERNAL_ID)
    mocker.patch("app.bootstrap.pathlib.Path.resolve", return_value=tmp_path)
    httpx_mock.add_response(
        method="POST", json={"id": "INS-1", "channel": {"identity": {"key": "value"}}}
    )

    bootstrap(test_settings)

    identity_file = tmp_path / f"{EXTERNAL_ID}_identity.json"
    assert json.loads(identity_file.read_text()) == {"key": "value"}
    ziti.run.assert_called_once()


def test_bootstrap_reuses_matching_identity_without_overwriting(
    tmp_path: Path,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
) -> None:
    """`bootstrap` keeps a matching identity file when the response carries no new identity."""
    ziti = mocker.patch("app.bootstrap.ziticorn")
    mocker.patch("app.bootstrap.get_instance_external_id", return_value=EXTERNAL_ID)
    mocker.patch("app.bootstrap.pathlib.Path.resolve", return_value=tmp_path)
    identity_file = tmp_path / f"{EXTERNAL_ID}_identity.json"
    original = {"mrok": {"extension": test_settings.mpt_extension_id}}
    identity_file.write_text(json.dumps(original))
    httpx_mock.add_response(method="POST", json={"id": "INS-2"})

    bootstrap(test_settings)

    assert json.loads(identity_file.read_text()) == original
    ziti.run.assert_called_once()


def test_bootstrap_replaces_identity_from_a_different_extension(
    tmp_path: Path,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
) -> None:
    """`bootstrap` requests and stores a new identity when the existing one is another extension."""
    mocker.patch("app.bootstrap.ziticorn")
    mocker.patch("app.bootstrap.get_instance_external_id", return_value=EXTERNAL_ID)
    mocker.patch("app.bootstrap.pathlib.Path.resolve", return_value=tmp_path)
    identity_file = tmp_path / f"{EXTERNAL_ID}_identity.json"
    identity_file.write_text(json.dumps({"mrok": {"extension": "EXT-0000-0000"}}))
    httpx_mock.add_response(
        method="POST", json={"id": "INS-3", "channel": {"identity": {"new": "identity"}}}
    )

    bootstrap(test_settings)

    assert json.loads(identity_file.read_text()) == {"new": "identity"}


@pytest.mark.transactional_db
async def test_get_affiliate_products_collects_unique_sorted_products(
    test_settings: Settings,
    account_factory: ModelFactory[Account],
) -> None:
    """Only active affiliate accounts contribute, and each product id appears once."""
    await account_factory(
        type=AccountType.AFFILIATE,
        status=AccountStatus.ACTIVE,
        products="PRD-2222-2222, PRD-1111-1111",
    )
    await account_factory(
        type=AccountType.AFFILIATE, status=AccountStatus.ACTIVE, products="PRD-1111-1111"
    )
    await account_factory(type=AccountType.AFFILIATE, status=AccountStatus.ACTIVE, products=None)
    await account_factory(
        type=AccountType.AFFILIATE, status=AccountStatus.DISABLED, products="PRD-8888-8888"
    )
    await account_factory(
        type=AccountType.OPERATIONS, status=AccountStatus.ACTIVE, products="PRD-9999-9999"
    )

    assert get_affiliate_products(test_settings) == ["PRD-1111-1111", "PRD-2222-2222"]


def test_get_affiliate_products_disposes_the_engine_on_failure(
    mocker: MockerFixture,
    test_settings: Settings,
) -> None:
    """The engine `bootstrap` opened is always closed, so the workers fork cleanly."""
    engine = mocker.MagicMock()
    engine.connect.side_effect = RuntimeError("no database")
    create_engine = mocker.patch("app.bootstrap.create_engine", return_value=engine)

    with pytest.raises(RuntimeError, match="no database"):
        get_affiliate_products(test_settings)

    create_engine.assert_called_once_with(str(test_settings.postgres_url))
    engine.dispose.assert_called_once_with()
