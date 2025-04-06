import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException
from src.services.auth import (
    create_access_token,
    create_refresh_token,
    update_refresh_token,
    get_email_from_token,
    verify_refresh_token,
)
from src.schemas import TokenDto
from src.database.models import User, RefreshToken
from src.conf.config import settings


@pytest.fixture
def mock_session():
    """
    Fixture to create a mock AsyncSession.
    """
    return AsyncMock()


@pytest.fixture
def test_user():
    """
    Fixture to create a test user.
    """
    return User(
        id=1,
        username="testuser",
        email="testuser@example.com",
        hashed_password="hashedpassword",
        confirmed=True,
    )


@pytest.fixture
def test_refresh_token():
    """
    Fixture to create a test refresh token.
    """
    return RefreshToken(
        id=1,
        token="test_refresh_token",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
        user_id=1,
    )


@pytest.mark.asyncio
async def test_create_access_token():
    """
    Test creating an access token.
    """
    # Setup
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=15)

    # Call method
    token = await create_access_token(data, int(expires_delta.total_seconds()))

    # Assertions
    assert isinstance(token, str)
    payload = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert payload["sub"] == "testuser"
    assert payload["token_type"] == "access"


@pytest.mark.asyncio
async def test_create_refresh_token(mock_session, test_user):
    """
    Test creating a refresh token.
    """
    # Setup
    data = {"sub": "testuser"}
    mock_refresh_token_service = AsyncMock()
    mock_refresh_token_service.create_refresh_token.return_value = RefreshToken(
        token="test_refresh_token",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
        user_id=1,
    )

    with patch(
        "src.services.auth.RefreshTokenService", return_value=mock_refresh_token_service
    ):
        # Call method
        result = await create_refresh_token(data, test_user.id, mock_session)

        # Assertions
        assert isinstance(result, RefreshToken)
        assert result.token == "test_refresh_token"
        mock_refresh_token_service.create_refresh_token.assert_awaited_once()


from unittest.mock import ANY


@pytest.mark.asyncio
async def test_update_refresh_token(mock_session, test_user, test_refresh_token):
    """
    Test updating a refresh token.
    """
    # Setup
    data = {"sub": "testuser"}
    token_dto = TokenDto(
        token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTc4MDIzNDIwOSwiaWF0IjoxNzQzOTQ2MjA5LCJ0b2tlbl90eXBlIjoicmVmcmVzaCJ9.vhXE9xbagG2humdNKIWFqDLy2n710bDcOjdG0dcwTyw",
        expires_at=datetime(2026, 5, 31, 13, 30, 9, 285116, tzinfo=timezone.utc),
        created_at=datetime(2025, 4, 6, 13, 30, 9, 285116, tzinfo=timezone.utc),
    )
    mock_refresh_token_service = AsyncMock()
    mock_refresh_token_service.update_refresh_token.return_value = test_refresh_token

    with patch(
        "src.services.auth.RefreshTokenService", return_value=mock_refresh_token_service
    ):
        # Call method
        result = await update_refresh_token(
            data, "old_refresh_token", test_user.id, mock_session
        )

        # Assertions
        assert isinstance(result, RefreshToken)
        assert result.token == "test_refresh_token"
        mock_refresh_token_service.update_refresh_token.assert_awaited_once_with(
            "old_refresh_token", ANY, test_user.id
        )


@pytest.mark.asyncio
async def test_get_email_from_token():
    """
    Test extracting email from a token.
    """
    # Setup
    data = {"sub": "testuser@example.com"}
    token = jwt.encode(data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    # Call method
    email = await get_email_from_token(token)

    # Assertions
    assert email == "testuser@example.com"


@pytest.mark.asyncio
async def test_get_email_from_token_invalid():
    """
    Test extracting email from an invalid token.
    """
    # Setup
    invalid_token = "invalid_token"

    # Call method and assert exception
    with pytest.raises(HTTPException) as exc_info:
        await get_email_from_token(invalid_token)

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Not valid token"


@pytest.mark.asyncio
async def test_verify_refresh_token(mock_session, test_user):
    """
    Test verifying a valid refresh token.
    """
    # Setup
    data = {"sub": "testuser", "token_type": "refresh"}
    token = jwt.encode(data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    mock_user_service = AsyncMock()
    mock_user_service.get_user_by_username_and_by_refresh_token.return_value = test_user

    with patch("src.services.auth.UserService", return_value=mock_user_service):
        # Call method
        user = await verify_refresh_token(token, mock_session)

        # Assertions
        assert user == test_user
        mock_user_service.get_user_by_username_and_by_refresh_token.assert_awaited_once_with(
            "testuser", token
        )


@pytest.mark.asyncio
async def test_verify_refresh_token_invalid(mock_session):
    """
    Test verifying an invalid refresh token.
    """
    # Setup
    invalid_token = "invalid_token"

    # Call method
    user = await verify_refresh_token(invalid_token, mock_session)

    # Assertions
    assert user is None
