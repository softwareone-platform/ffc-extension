import pytest
import pytest_mock

from app.logging import get_logging_config, setup_logging


@pytest.mark.parametrize(
    ("debug", "expected_log_level"),
    [
        (True, "DEBUG"),
        (False, "INFO"),
    ],
)
@pytest.mark.parametrize(
    ("cli_rich_logging", "expected_handler"),
    [
        (True, "rich"),
        (False, "console"),
    ],
)
def test_get_logging_config_level(
    mocker: pytest_mock.MockerFixture,
    debug: bool,
    expected_log_level: str,
    cli_rich_logging: bool,
    expected_handler: str,
):
    settings = mocker.MagicMock()
    settings.cli_rich_logging = cli_rich_logging
    settings.debug = debug

    logging_config = get_logging_config(settings=settings)
    for logger_config in logging_config["loggers"].values():
        assert logger_config["level"] == expected_log_level
        assert logger_config["handlers"] == [expected_handler]


def test_setup_logging(mocker: pytest_mock.MockerFixture):
    mocker.patch("app.logging.get_logging_config", return_value={"logging": "config"})
    mocked_dictconfig = mocker.patch("app.logging.logging.config.dictConfig")

    setup_logging(mocker.MagicMock)

    mocked_dictconfig.assert_called_once_with({"logging": "config"})
