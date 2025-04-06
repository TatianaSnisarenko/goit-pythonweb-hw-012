import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone
from src.services.refresh_tokens import RefreshTokenService
from src.schemas import TokenDto
from src.database.models import RefreshToken


@pytest.fixture
def mock_repository():
    """
    Fixture to create a mock RefreshTokenRepository.
    """
    return AsyncMock()


@pytest.fixture
def refresh_token_service(mock_repository):
    """
    Fixture to create a RefreshTokenService with a mocked repository.
    """
    service = RefreshTokenService(db=None)
    service.repository = mock_repository
    return service


@pytest.fixture
def test_token_dto():
    """
    Fixture to create a test TokenDto object.
    """
    return TokenDto(
        token="new_refresh_token",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def test_refresh_token():
    """
    Fixture to create a test RefreshToken object.
    """
    return RefreshToken(
        id=1,
        token="new_refresh_token",
        expires_at=datetime.utcnow() + timedelta(days=7),
        created_at=datetime.utcnow(),
        user_id=1,
    )


@pytest.mark.asyncio
async def test_create_refresh_token(
    refresh_token_service, mock_repository, test_token_dto, test_refresh_token
):
    """
    Test creating a new refresh token.
    """
    # Setup
    mock_repository.create_refresh_token.return_value = test_refresh_token

    # Call method
    result = await refresh_token_service.create_refresh_token(test_token_dto, user_id=1)

    # Assertions
    assert result == test_refresh_token
    mock_repository.create_refresh_token.asssert_awaited_once()


@pytest.mark.asyncio
async def test_update_refresh_token(
    refresh_token_service, mock_repository, test_token_dto, test_refresh_token
):
    """
    Test updating an existing refresh token.
    """
    # Setup
    mock_repository.update_refresh_token.return_value = test_refresh_token

    # Call method
    result = await refresh_token_service.update_refresh_token(
        old_refresh_token="old_refresh_token", refresh_token=test_token_dto, user_id=1
    )

    # Assertions
    assert result == test_refresh_token
    mock_repository.update_refresh_token.assert_awaited_once()


def test_map_refresh_token(refresh_token_service, test_token_dto):
    """
    Test mapping a TokenDto to a RefreshToken model.
    """
    # Call method
    result = refresh_token_service.map_refresh_token(test_token_dto, user_id=1)

    # Assertions
    assert isinstance(result, RefreshToken)
    assert result.token == test_token_dto.token
    assert result.expires_at == test_token_dto.expires_at
    assert result.created_at == test_token_dto.created_at
    assert result.user_id == 1
