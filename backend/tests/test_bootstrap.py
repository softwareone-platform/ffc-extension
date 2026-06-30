import json
from pathlib import Path

from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from app.bootstrap import bootstrap
from app.conf import Settings

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
    mocker.patch("app.bootstrap.pathlib.Path.cwd", return_value=tmp_path)
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
    mocker.patch("app.bootstrap.pathlib.Path.cwd", return_value=tmp_path)
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
    mocker.patch("app.bootstrap.pathlib.Path.cwd", return_value=tmp_path)
    identity_file = tmp_path / f"{EXTERNAL_ID}_identity.json"
    identity_file.write_text(json.dumps({"mrok": {"extension": "EXT-0000-0000"}}))
    httpx_mock.add_response(
        method="POST", json={"id": "INS-3", "channel": {"identity": {"new": "identity"}}}
    )

    bootstrap(test_settings)

    assert json.loads(identity_file.read_text()) == {"new": "identity"}
