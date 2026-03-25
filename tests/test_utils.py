from pytest_mock import MockerFixture

from app.conf import Settings
from app.utils import send_email


def test_send_email_success(test_settings: Settings, mocker: MockerFixture):
    mock_smtp = mocker.patch("smtplib.SMTP")
    mock_server = mocker.MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    recipient_email = "recipient@example.com"
    recipient_name = "Recipient Name"
    subject = "Test Subject"
    html_message = "<h1>Hello</h1>"

    send_email(test_settings, recipient_email, recipient_name, subject, html_message)

    mock_smtp.assert_called_with("smtp.example.com", 587)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user", "password")
    mock_server.sendmail.assert_called_once()
    args, kwargs = mock_server.sendmail.call_args
    assert args[0] == "test@example.com"
    assert args[1] == "recipient@example.com"
    assert subject in args[2]
    assert html_message in args[2]
