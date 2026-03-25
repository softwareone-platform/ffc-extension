import pytest
from pytest_mock import MockerFixture

from app.conf import Settings


@pytest.fixture(autouse=True)
def mock_cli_settings(mocker: MockerFixture, test_settings: Settings) -> None:
    mocker.patch("app.cli.get_settings", return_value=test_settings)
