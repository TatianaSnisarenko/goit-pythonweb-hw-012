import pytest
from unittest.mock import ANY, AsyncMock, patch
from fastapi_mail.errors import ConnectionErrors
from src.services.email import send_confirm_email, send_reset_password_email, send_email
from src.services.auth import create_email_token
from pydantic import EmailStr


@pytest.fixture
def mock_fastmail():
    """
    Fixture to mock FastMail.
    """
    return AsyncMock()


@pytest.fixture
def mock_create_email_token():
    """
    Fixture to mock create_email_token.
    """
    with patch(
        "src.services.auth.create_email_token", return_value="mocked_token"
    ) as mock:
        yield mock


@pytest.mark.asyncio
async def test_send_confirm_email(mock_fastmail, mock_create_email_token):
    """
    Test sending a confirmation email.
    """
    with patch("src.services.email.FastMail", return_value=mock_fastmail):
        # Call the function
        await send_confirm_email(
            email="testuser@example.com",
            username="testuser",
            host="http://localhost",
        )

        # Assertions
        mock_fastmail.send_message.assert_awaited_once()
        assert (
            mock_fastmail.send_message.call_args[1]["template_name"]
            == "verify_email.html"
        )


@pytest.mark.asyncio
async def test_send_reset_password_email(mock_fastmail, mock_create_email_token):
    """
    Test sending a password reset email.
    """
    with patch("src.services.email.FastMail", return_value=mock_fastmail):
        # Call the function
        await send_reset_password_email(
            email="testuser@example.com",
            username="testuser",
            host="http://localhost",
        )

        # Assertions
        mock_fastmail.send_message.assert_awaited_once()
        assert (
            mock_fastmail.send_message.call_args[1]["template_name"]
            == "reset_password.html"
        )


@pytest.mark.asyncio
async def test_send_email(mock_fastmail, mock_create_email_token):
    """
    Test sending a generic email.
    """
    with patch("src.services.email.FastMail", return_value=mock_fastmail):
        # Call the function
        await send_email(
            email="testuser@example.com",
            subject="Test Subject",
            template_name="test_template.html",
            username="testuser",
            host="http://localhost",
        )

        # Assertions
        mock_fastmail.send_message.assert_awaited_once()
        assert (
            mock_fastmail.send_message.call_args[1]["template_name"]
            == "test_template.html"
        )


@pytest.mark.asyncio
async def test_send_email_connection_error(mock_fastmail, mock_create_email_token):
    """
    Test handling a connection error when sending an email.
    """
    with patch("src.services.email.FastMail", return_value=mock_fastmail):
        # Simulate a connection error
        mock_fastmail.send_message.side_effect = ConnectionErrors("Connection error")

        # Call the function
        with patch("builtins.print") as mock_print:
            await send_email(
                email="testuser@example.com",
                subject="Test Subject",
                template_name="test_template.html",
                username="testuser",
                host="http://localhost",
            )

            # Assertions
            mock_fastmail.send_message.assert_awaited_once()
            mock_print.assert_called_once()
