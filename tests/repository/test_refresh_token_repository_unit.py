import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import RefreshToken
from src.repository.refresh_tokens import RefreshTokenRepository


@pytest.fixture
def mock_session():
    """
    Fixture to create a mock AsyncSession.
    """
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def refresh_token_repository(mock_session):
    """
    Fixture to create a RefreshTokenRepository with a mock session.
    """
    return RefreshTokenRepository(mock_session)


@pytest.fixture
def test_refresh_token():
    """
    Fixture to create a test refresh token.
    """
    return RefreshToken(
        id=1,
        token="test_refresh_token",
        user_id=1,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_create_refresh_token(
    refresh_token_repository, mock_session, test_refresh_token
):
    """
    Test creating a new refresh token.
    """

    # Call the actual method
    result = await refresh_token_repository.create_refresh_token(test_refresh_token)

    # Assertions
    assert isinstance(result, RefreshToken)
    assert result.token == "test_refresh_token"
    assert result.user_id == 1
    mock_session.add.assert_called_once_with(test_refresh_token)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(test_refresh_token)


@pytest.mark.asyncio
async def test_update_refresh_token(
    refresh_token_repository, mock_session, test_refresh_token
):
    """
    Test updating an existing refresh token.
    """
    # Setup
    new_refresh_token = RefreshToken(
        token="new_refresh_token",
        expires_at=datetime.now(timezone.utc) + timedelta(days=14),
        created_at=datetime.now(timezone.utc),
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_refresh_token
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call the actual method
    result = await refresh_token_repository.update_refresh_token(
        old_refresh_token="test_refresh_token",
        refresh_token=new_refresh_token,
        user_id=1,
    )

    # Assertions
    assert result is not None
    assert result.token == "new_refresh_token"
    assert result.expires_at == new_refresh_token.expires_at
    assert result.created_at == new_refresh_token.created_at
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(test_refresh_token)


@pytest.mark.asyncio
async def test_update_refresh_token_not_found(refresh_token_repository, mock_session):
    """
    Test updating a refresh token that does not exist.
    """
    # Setup
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Call the actual method
    result = await refresh_token_repository.update_refresh_token(
        old_refresh_token="nonexistent_token",
        refresh_token=RefreshToken(
            token="new_refresh_token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=14),
            created_at=datetime.now(timezone.utc),
        ),
        user_id=1,
    )

    # Assertions
    assert result is None
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_not_awaited()
    mock_session.refresh.assert_not_awaited()
