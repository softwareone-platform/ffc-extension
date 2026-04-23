import pytest
from app.conf import Settings
from pytest_mock import MockerFixture


@pytest.fixture(autouse=True)
def mock_cli_settings(mocker: MockerFixture, test_settings: Settings) -> None:
    mocker.patch("app.cli.get_settings", return_value=test_settings)
