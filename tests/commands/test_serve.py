import multiprocessing

from pytest_mock import MockerFixture
from typer.testing import CliRunner

from app.cli import app
from app.main import app as fastapi_app


def test_serve(mocker: MockerFixture):
    mocker.patch(
        "app.commands.serve.get_logging_config",
        return_value={"logging": "config"},
    )
    mocked_app = mocker.MagicMock()
    mocked_standalone_app = mocker.patch(
        "app.commands.serve.StandaloneApplication", return_value=mocked_app
    )
    runner = CliRunner()
    result = runner.invoke(app, ["serve"])
    assert result.exit_code == 0
    mocked_standalone_app.assert_called_once_with(
        fastapi_app,
        {
            "bind": "127.0.0.1:8000",
            "workers": (multiprocessing.cpu_count() * 2) + 1,
            "worker_class": "uvicorn.workers.UvicornWorker",
            "logconfig_dict": {"logging": "config"},
            "reload": False,
        },
    )
    mocked_app.run.assert_called_once()


def test_serve_with_options(mocker: MockerFixture):
    mocker.patch(
        "app.commands.serve.get_logging_config",
        return_value={"logging": "config"},
    )
    mocker.patch("app.commands.serve.number_of_workers", return_value=4)
    mocked_standalone_app = mocker.patch("app.commands.serve.StandaloneApplication")
    runner = CliRunner()
    result = runner.invoke(
        app, ["serve", "--host", "0.0.0.0", "--port", "8080", "--workers", "2", "--reload"]
    )
    assert result.exit_code == 0
    mocked_standalone_app.assert_called_once_with(
        fastapi_app,
        {
            "bind": "0.0.0.0:8080",
            "workers": 2,
            "worker_class": "uvicorn.workers.UvicornWorker",
            "logconfig_dict": {"logging": "config"},
            "reload": True,
        },
    )
