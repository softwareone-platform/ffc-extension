import json
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
import yaml

from app.openapi import generate_openapi_spec


class OutputFormat(str, Enum):
    json = "json"
    yaml = "yaml"


def command(
    ctx: typer.Context,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output file",
        ),
    ] = Path("ffc_operations_openapi_spec.yml"),
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            "--output-format",
            "-f",
            help="Output file format",
        ),
    ] = OutputFormat.yaml,
):
    """
    Generates the OpenAPI spec file.
    """
    from app import main

    dump_fn = json.dump if output_format == OutputFormat.json else yaml.dump
    spec = generate_openapi_spec(main.app, ctx.obj)

    with open(output, "w") as f:  # type: ignore
        dump_fn(spec, f, indent=2)
