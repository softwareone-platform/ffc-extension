import pytest
from pytest_mock import MockerFixture

from app.conf import Settings
from app.db.base import verify_db_connection


async def test_verify_db_connection_raises_when_select_returns_unexpected_value(
    test_settings: Settings, mocker: MockerFixture
) -> None:
    """`verify_db_connection` raises `RuntimeError` when `SELECT 1` does not return 1."""
    result = mocker.Mock()
    result.one.return_value = [2]
    session = mocker.AsyncMock()
    session.execute.return_value = result
    session_cm = mocker.MagicMock()
    session_cm.__aenter__.return_value = session
    mocker.patch("app.db.base.session_factory", return_value=session_cm)

    with pytest.raises(RuntimeError, match="Could not verify database connection"):
        await verify_db_connection(test_settings)
