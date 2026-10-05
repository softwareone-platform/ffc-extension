from fastapi import FastAPI
from pytest_mock import MockerFixture

from app.conf import Settings
from app.fastapi import setup_app
from app.openapi import generate_openapi_spec


def test_gen_openapi(fastapi_app: FastAPI, test_settings: Settings):
    spec = generate_openapi_spec(setup_app(), test_settings)
    assert "## Available RQL filters" in spec["paths"]["/ops/v1/accounts"]["get"]["description"]


def test_app_openapi_serves_generated_spec(mocker: MockerFixture, test_settings: Settings) -> None:
    """`app.openapi()` returns the spec built by `generate_openapi_spec` for that app."""
    spec = {"openapi": "3.1.0"}
    generate = mocker.patch("app.fastapi.generate_openapi_spec", return_value=spec)
    app = setup_app()

    assert app.openapi() == spec
    generate.assert_called_once_with(app, test_settings)
