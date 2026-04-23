from app.cli import app
from pytest_mock import MockerFixture
from typer.testing import CliRunner


def test_shell(mocker: MockerFixture):
    mocked_ishell = mocker.patch("app.commands.shell.InteractiveShellEmbed")
    runner = CliRunner()
    result = runner.invoke(app, ["shell"])
    assert result.exit_code == 0
    mocked_ishell.assert_called_once()
