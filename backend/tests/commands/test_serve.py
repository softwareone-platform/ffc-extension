from app.cli import app
from pytest_mock import MockerFixture
from typer.testing import CliRunner


def test_serve(mocker: MockerFixture):
    mocked_settings = mocker.MagicMock()
    mocker.patch("app.cli.get_settings", return_value=mocked_settings)
    mocked_bootstrap = mocker.patch("app.commands.serve.bootstrap")
    runner = CliRunner()
    result = runner.invoke(app, ["serve"])
    assert result.exit_code == 0
    mocked_bootstrap.assert_called_once_with(
        mocked_settings,
        ziti_load_timeout_ms=20_000,
        server_workers=mocker.ANY,
        server_reload=False,
        server_backlog=2048,
        server_timeout_keep_alive=5,
        server_limit_concurrency=None,
        server_limit_max_requests=None,
        events_metrics_collect_interval=5.0,
        events_publishers_port=50000,
        events_subscribers_port=50001,
    )


def test_serve_with_options(mocker: MockerFixture):
    mocked_settings = mocker.MagicMock()
    mocker.patch("app.cli.get_settings", return_value=mocked_settings)
    mocked_bootstrap = mocker.patch("app.commands.serve.bootstrap")
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "serve",
            "--ziti-load-timeout-ms",
            "5000",
            "--server-workers",
            "2",
            "--server-backlog",
            "1024",
            "--server-timeout-keep-alive",
            "10",
            "--server-limit-concurrency",
            "13",
            "--server-limit-max-requests",
            "1001",
            "--server-reload",
            "--events-publishers-port",
            "9000",
            "--events-subscribers-port",
            "9001",
            "--events-metrics-collect-interval",
            "12.4",
        ],
    )
    assert result.exit_code == 0
    mocked_bootstrap.assert_called_once_with(
        mocked_settings,
        ziti_load_timeout_ms=5000,
        server_workers=2,
        server_reload=True,
        server_backlog=1024,
        server_timeout_keep_alive=10,
        server_limit_concurrency=13,
        server_limit_max_requests=1001,
        events_metrics_collect_interval=12.4,
        events_publishers_port=9000,
        events_subscribers_port=9001,
    )
