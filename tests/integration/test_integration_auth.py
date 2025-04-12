from unittest.mock import AsyncMock, Mock

import pytest
from src.services.auth import create_access_token
from tests.integration.test_utils import create_user

from fastapi import status


def test_registration(client, monkeypatch):
    """
    Test user registration.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_confirm_email", mock_send_email)

    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "Password123!",
    }

    response = client.post(
        "api/auth/register",
        json=user_data,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert data["role"] == "user"
    assert "hashed_password" not in data
    assert "avatar" in data


def test_repeat_register(client, test_user_not_confirmed):
    """
    Test repeated user registration with the same email.
    """
    response = client.post(
        "api/auth/register",
        json={
            "username": test_user_not_confirmed.get("username"),
            "email": test_user_not_confirmed.get("email"),
            "password": test_user_not_confirmed.get("password"),
        },
    )
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["message"] == "User with such email already exists"


def test_not_confirmed_login(client, test_user_not_confirmed):
    """
    Test login with an unconfirmed email.
    """
    response = client.post(
        "api/auth/login",
        data={
            "username": test_user_not_confirmed.get("username"),
            "password": test_user_not_confirmed.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["message"] == "Email must be confirmed"


@pytest.mark.asyncio
async def test_login_with_confirmed_email(client, test_user_confirmed):
    """
    Test login with a confirmed email.
    """
    response = client.post(
        "api/auth/login",
        data={
            "username": test_user_confirmed.get("username"),
            "password": test_user_confirmed.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_wrong_password_login(client, test_user_confirmed):
    """
    Test login with a wrong password.
    """
    response = client.post(
        "api/auth/login",
        data={
            "username": test_user_confirmed.get("username"),
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["message"] == "Not valid password or username"


@pytest.mark.asyncio
async def test_wrong_username_login(client, test_user_confirmed):
    """
    Test login with a wrong username.
    """
    response = client.post(
        "api/auth/login",
        data={
            "username": "wrongusername",
            "password": test_user_confirmed.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["message"] == "Not valid password or username"


def test_validation_error_login(client, test_user_confirmed):
    """
    Test login with missing required fields.
    """
    response = client.post(
        "api/auth/login",
        data={"password": test_user_confirmed.get("password")},
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_confirmed_email_success(client):
    """
    Test successful email confirmation.
    """
    email = await create_user()
    token = await create_access_token(data={"sub": email})
    response = client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["message"] == "Email confirmed successfully"


@pytest.mark.asyncio
async def test_confirmed_email_already_confirmed(client, test_user_confirmed):
    """
    Test email confirmation when the email is already confirmed.
    """
    token = await create_access_token(data={"sub": test_user_confirmed["email"]})
    response = client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["message"] == "Your email is already confirmed"


@pytest.mark.asyncio
async def test_confirmed_email_user_not_found_by_email(client):
    """
    Test email confirmation with an invalid token.
    """
    token = await create_access_token(data={"sub": "some@example.com"})
    response = client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
    data = response.json()
    assert data["message"] == "Verification error"


@pytest.mark.asyncio
async def test_confirmed_email_invalid_token(client):
    """
    Test email confirmation with an invalid token.
    """
    token = "invalid_token"
    response = client.get(f"/api/auth/confirmed_email/{token}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text


@pytest.mark.asyncio
async def test_request_email_success(client, monkeypatch):
    """
    Test successful email request for a not confirmed user email.
    """
    email = await create_user()

    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_confirm_email", mock_send_email)

    response = client.post(
        "/api/auth/request-email",
        json={"email": email},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["message"] == "Check your mailbox for confirmation email"

    mock_send_email.assert_called_once()


@pytest.mark.asyncio
async def test_request_email_already_confirmed(
    client, monkeypatch, test_user_confirmed
):
    """
    Test successful email request for a confirmed user.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_confirm_email", mock_send_email)

    response = client.post(
        "/api/auth/request-email",
        json={"email": test_user_confirmed["email"]},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["message"] == "Your email is already confirmed"

    mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_request_email_user_not_found(client, monkeypatch):
    """
    Test email request for a non-existent user.
    """

    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_confirm_email", mock_send_email)

    response = client.post(
        "/api/auth/request-email",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
    data = response.json()
    assert data["message"] == "Verification error"

    mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_request_email_invalid_email(client, monkeypatch):
    """
    Test email request with an invalid email format.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_confirm_email", mock_send_email)

    response = client.post(
        "/api/auth/request-email",
        json={"email": "invalid-email"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, response.text
    data = response.json()
    assert "detail" in data

    mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_request_success(client, monkeypatch, test_user_confirmed):
    """
    Test successful password reset request for a confirmed user.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_reset_password_email", mock_send_email)

    response = client.post(
        "/api/auth/reset-password-request",
        json={"email": test_user_confirmed["email"]},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["message"] == "Check your mailbox for reset password email"

    mock_send_email.assert_called_once()


@pytest.mark.asyncio
async def test_reset_password_request_user_not_found(client, monkeypatch):
    """
    Test password reset request for a non-existent user.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_reset_password_email", mock_send_email)

    response = client.post(
        "/api/auth/reset-password-request",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
    data = response.json()
    assert data["message"] == "Verification error"

    mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_request_email_not_confirmed(
    client, monkeypatch, test_user_not_confirmed
):
    """
    Test password reset request for a user whose email is not confirmed.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_reset_password_email", mock_send_email)

    response = client.post(
        "/api/auth/reset-password-request",
        json={"email": test_user_not_confirmed["email"]},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED, response.text
    data = response.json()
    assert data["message"] == "Email must be confirmed"

    mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_success(client, monkeypatch, get_token_confirmed):
    """
    Test successful password reset for a confirmed user.
    """
    email = await create_user(confirmed=True)

    mock_get_email_from_token = AsyncMock(return_value=email)
    monkeypatch.setattr("src.api.auth.get_email_from_token", mock_get_email_from_token)

    response = client.post(
        "/api/auth/reset-password",
        data={"token": "valid_token", "new_password": "NewPassword123!"},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["message"] == "Password has been reset successfully"

    mock_get_email_from_token.assert_called_once()


@pytest.mark.asyncio
async def test_reset_password_missing_data(client):
    """
    Test password reset with missing token or new password.
    """
    # Send the reset password request with missing data
    response = client.post(
        "/api/auth/reset-password",
        data={"token": "valid_token"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
    data = response.json()
    assert data["message"] == "Invalid data"

    response = client.post(
        "/api/auth/reset-password",
        data={"new_password": "NewPassword123!"},  # Missing token
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
    data = response.json()
    assert data["message"] == "Invalid data"


@pytest.mark.asyncio
async def test_reset_password_user_not_found(client, monkeypatch):
    """
    Test password reset for a non-existent user.
    """
    # Mock the get_email_from_token function
    mock_get_email_from_token = AsyncMock(return_value="nonexistent@example.com")
    monkeypatch.setattr("src.api.auth.get_email_from_token", mock_get_email_from_token)

    # Send the reset password request
    response = client.post(
        "/api/auth/reset-password",
        data={"token": "valid_token", "new_password": "NewPassword123!"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
    data = response.json()
    assert data["message"] == "Verification error"

    # Verify that the mocked function was called
    mock_get_email_from_token.assert_called_once()


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client, monkeypatch):
    """
    Test password reset with an invalid token.
    """
    # Mock the get_email_from_token to return None
    mock_get_email_from_token = AsyncMock(return_value=None)
    monkeypatch.setattr("src.api.auth.get_email_from_token", mock_get_email_from_token)

    # Send the reset password request
    response = client.post(
        "/api/auth/reset-password",
        data={"token": "invalid_token", "new_password": "NewPassword123!"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST, response.text
    data = response.json()
    assert data["message"] == "Verification error"

    # Verify that the mocked function was called
    mock_get_email_from_token.assert_called_once()
