from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.dependencies.utils import get_flat_dependant
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from snippettoni.injector import inject_code_samples
from snippettoni.renderer import SnippetRenderer
from starlette.routing import BaseRoute

from app.conf import Settings
from app.rql import RQLQuery


def iter_api_routes(routes: list[BaseRoute]) -> Iterator[APIRoute]:
    for r in routes:
        if isinstance(r, APIRoute):
            yield r
        inc = getattr(r, "original_router", None)
        if inc is not None:
            yield from iter_api_routes(inc.routes)
            continue
        sub = getattr(r, "routes", None)
        if sub:
            yield from iter_api_routes(sub)


def generate_openapi_spec(app: FastAPI, settings: Settings):
    if app.openapi_schema:  # pragma: no cover
        return app.openapi_schema

    for api_route in iter_api_routes(app.routes):
        flat_dependant = get_flat_dependant(api_route.dependant, skip_repeats=True)
        for dependency in flat_dependant.dependencies:
            call = dependency.call
            if call is not None and isinstance(call, RQLQuery):
                api_route.description = (
                    f"{api_route.description or ''}\n\n"
                    "## Available RQL filters\n\n"
                    f"{call.rules.get_documentation()}"
                )

    spec = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        tags=app.openapi_tags,
        routes=app.routes,
    )
    spec = inject_code_samples(
        spec,
        SnippetRenderer(),
        settings.api_base_url,
    )
    app.openapi_schema = spec
    return app.openapi_schema
