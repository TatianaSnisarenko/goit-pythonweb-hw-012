from unittest.mock import Mock
import pytest
from sqlalchemy import select
from src.database.models import User
from tests.conftest import TestingSessionLocal


user_data = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "Password123!",
    "role": "user",
}


def test_registration(client, monkeypatch):
    """
    Test user registration.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_confirm_email", mock_send_email)

    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hashed_password" not in data
    assert "avatar" in data


def test_repeat_register(client, monkeypatch):
    """
    Test repeated user registration with the same email.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_confirm_email", mock_send_email)

    response = client.post("api/auth/register", json=user_data)
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["message"] == "User with such email already exists"


def test_not_confirmed_login(client, monkeypatch):
    """
    Test login with an unconfirmed email.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_confirm_email", mock_send_email)

    response = client.post("api/auth/register", json=user_data)
    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["message"] == "Email must be confirmed"


@pytest.mark.asyncio
async def test_login(client, monkeypatch):
    """
    Test login with a confirmed email.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_confirm_email", mock_send_email)

    unique_user_data = {
        "username": "testuser1",
        "email": "testuser1@example.com",
        "password": "Password123!",
        "role": "user",
    }
    # Register a new user
    response = client.post("api/auth/register", json=unique_user_data)
    assert response.status_code == 201, response.text

    # Update the user to confirm the email
    async with TestingSessionLocal() as session:
        user = await session.execute(
            select(User).where(User.email == unique_user_data["email"])
        )
        user = user.scalar_one_or_none()
        assert user is not None, "User not found in the database"
        user.confirmed = True
        await session.commit()

    # Login with the confirmed user
    response = client.post(
        "api/auth/login",
        data={
            "username": unique_user_data.get("username"),
            "password": unique_user_data.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data


@pytest.mark.asyncio
async def test_wrong_password_login(client, monkeypatch):
    """
    Test login with a wrong password.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_confirm_email", mock_send_email)

    unique_user_data = {
        "username": "testuser2",
        "email": "testuser2@example.com",
        "password": "Password123!",
        "role": "user",
    }

    # Register a new user
    response = client.post("api/auth/register", json=unique_user_data)
    assert response.status_code == 201, response.text

    # Update the user to confirm the email
    async with TestingSessionLocal() as session:
        user = await session.execute(
            select(User).where(User.email == unique_user_data["email"])
        )
        user = user.scalar_one_or_none()
        assert user is not None, "User not found in the database"
        user.confirmed = True
        await session.commit()

    response = client.post(
        "api/auth/login",
        data={
            "username": unique_user_data.get("username"),
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["message"] == "Not valid password or username"


@pytest.mark.asyncio
async def test_wrong_username_login(client, monkeypatch):
    """
    Test login with a wrong username.
    """
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_confirm_email", mock_send_email)

    unique_user_data = {
        "username": "testuser3",
        "email": "testuser3@example.com",
        "password": "Password123!",
        "role": "user",
    }
    # Register a new user
    response = client.post("api/auth/register", json=unique_user_data)
    assert response.status_code == 201, response.text

    # Update the user to confirm the email
    async with TestingSessionLocal() as session:
        user = await session.execute(
            select(User).where(User.email == unique_user_data["email"])
        )
        user = user.scalar_one_or_none()
        assert user is not None, "User not found in the database"
        user.confirmed = True
        await session.commit()

    response = client.post(
        "api/auth/login",
        data={
            "username": "wrongusername",
            "password": unique_user_data.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["message"] == "Not valid password or username"


def test_validation_error_login(client):
    """
    Test login with missing required fields.
    """
    response = client.post(
        "api/auth/login",
        data={"password": user_data.get("password")},
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data
