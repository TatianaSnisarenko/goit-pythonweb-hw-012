from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import create_email_token
from src.conf.config import settings

"""
Email service module.

This module provides functionality for sending emails, including email 
confirmation and password reset emails. It uses FastAPI-Mail for email 
delivery and supports HTML templates for email content.

Functions:
    send_confirm_email: Sends an email confirmation message to a user.
    send_reset_password_email: Sends a password reset email to a user.
    send_email: A generic function for sending emails with a specified template.
"""

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates",
)


async def send_confirm_email(email: EmailStr, username: str, host: str) -> None:
    """
    Sends an email confirmation message to a user.

    Args:
        email (EmailStr): The recipient's email address.
        username (str): The username of the recipient.
        host (str): The host URL for generating the confirmation link.

    Returns:
        None
    """
    await send_email(
        email=email,
        subject="Confirm your email",
        template_name="verify_email.html",
        username=username,
        host=host,
    )


async def send_reset_password_email(email: EmailStr, username: str, host: str) -> None:
    """
    Sends a password reset email to a user.

    Args:
        email (EmailStr): The recipient's email address.
        username (str): The username of the recipient.
        host (str): The host URL for generating the password reset link.

    Returns:
        None
    """
    await send_email(
        email=email,
        subject=f"Reset password request for user {username}",
        template_name="reset_password.html",
        username=username,
        host=host,
    )


async def send_email(
    email: EmailStr, subject: str, template_name: str, username: str, host: str
) -> None:
    """
    A generic function for sending emails with a specified template.

    Args:
        email (EmailStr): The recipient's email address.
        subject (str): The subject of the email.
        template_name (str): The name of the HTML template to use for the email content.
        username (str): The username of the recipient.
        host (str): The host URL for generating links in the email.

    Returns:
        None

    Raises:
        ConnectionErrors: If there is an error connecting to the email server.
    """
    try:
        token_verification = create_email_token({"sub": email})
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name=template_name)
    except ConnectionErrors as err:
        print(err)
