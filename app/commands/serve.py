import multiprocessing
from typing import Annotated

import typer

from app.bootstrap import bootstrap


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


default_workers = number_of_workers()


def command(
    ctx: typer.Context,
    ziti_load_timeout_ms: Annotated[
        int,
        typer.Option(
            "--ziti-load-timeout-ms",
            help="Timeout (ms) waiting for Ziti to load.",
            show_default=True,
        ),
    ] = 20_000,
    server_workers: Annotated[
        int,
        typer.Option(
            "--server-workers",
            "-w",
            help=f"Number of workers. Default: {default_workers}",
            show_default=True,
        ),
    ] = default_workers,
    server_backlog: Annotated[
        int,
        typer.Option(
            "--server-backlog",
            help="TCP socket listen backlog.",
            show_default=True,
        ),
    ] = 2048,
    server_timeout_keep_alive: Annotated[
        int,
        typer.Option(
            "--server-timeout-keep-alive",
            help="Seconds to keep idle HTTP connections open.",
            show_default=True,
        ),
    ] = 5,
    server_limit_concurrency: Annotated[
        int | None,
        typer.Option(
            "--server-limit-concurrency",
            help="Maximum number of concurrent requests per worker.",
            show_default=True,
        ),
    ] = None,
    server_limit_max_requests: Annotated[
        int | None,
        typer.Option(
            "--server-limit-max-requests",
            help="Restart a worker after handling this many requests.",
            show_default=True,
        ),
    ] = None,
    server_reload: Annotated[
        bool,
        typer.Option(
            "--server-reload",
            "-r",
            help="Enable server auto-reload. Default: False",
            show_default=True,
        ),
    ] = False,
    events_publishers_port: Annotated[
        int,
        typer.Option(
            "--events-publishers-port",
            help=(
                "TCP port where the mrok agent "
                "should connect to publish to request/response messages."
            ),
            show_default=True,
        ),
    ] = 50000,
    events_subscribers_port: Annotated[
        int,
        typer.Option(
            "--events-subscribers-port",
            help=(
                "TCP port where the mrok agent should listen for incoming subscribers "
                "connections for request/response messages."
            ),
            show_default=True,
        ),
    ] = 50001,
    events_metrics_collect_interval: Annotated[
        float,
        typer.Option(
            "--events-metrics-collect-interval",
            help="Interval in seconds between events metrics collect.",
            show_default=True,
        ),
    ] = 5.0,
):
    """Run the extension."""
    bootstrap(
        ctx.obj,
        ziti_load_timeout_ms=ziti_load_timeout_ms,
        server_workers=server_workers,
        server_reload=server_reload,
        server_backlog=server_backlog,
        server_timeout_keep_alive=server_timeout_keep_alive,
        server_limit_concurrency=server_limit_concurrency,
        server_limit_max_requests=server_limit_max_requests,
        events_metrics_collect_interval=events_metrics_collect_interval,
        events_publishers_port=events_publishers_port,
        events_subscribers_port=events_subscribers_port,
    )
