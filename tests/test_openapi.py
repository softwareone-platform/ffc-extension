from fastapi import FastAPI

from app.conf import Settings
from app.openapi import generate_openapi_spec


def test_gen_openapi(fastapi_app: FastAPI, test_settings: Settings):
    spec = generate_openapi_spec(fastapi_app, test_settings)
    assert "## Available RQL filters" in spec["paths"]["/accounts"]["get"]["description"]
