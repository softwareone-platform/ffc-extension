from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from snippettoni.injector import inject_code_samples
from snippettoni.renderer import SnippetRenderer
from starlette.routing import BaseRoute

from app.conf import Settings
from app.rql import RQLQuery


def iter_flat_dependencies(dependant: Dependant) -> Iterator[Dependant]:
    for sub_dependant in dependant.dependencies:
        yield sub_dependant
        yield from iter_flat_dependencies(sub_dependant)


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
        for dependency in iter_flat_dependencies(api_route.dependant):
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
