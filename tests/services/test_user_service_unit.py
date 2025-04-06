import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.users import UserService
from src.schemas import User, UserCreate


@pytest.fixture
def mock_repository():
    """
    Fixture to create a mock UserRepository.
    """
    return AsyncMock()


@pytest.fixture
def user_service(mock_repository):
    """
    Fixture to create a UserService with a mocked repository.
    """
    service = UserService(db=None)
    service.repository = mock_repository
    return service


@pytest.fixture
def test_user():
    """
    Fixture to create a test user.
    """
    return User(
        id=1,
        username="testuser",
        email="testuser@example.com",
        hashed_password="Hashedpassword1!",
        confirmed=True,
        role="user",
        avatar="http://gravatar.com/avatar",
    )


@pytest.mark.asyncio
async def test_create_user(user_service, mock_repository):
    """
    Test creating a new user with Gravatar avatar.
    """
    # Setup
    user_data = UserCreate(
        username="newuser",
        email="newuser@example.com",
        password="Hashedpassword1!",
        role="user",
    )
    created_user = User(
        id=2,
        username="newuser",
        email="newuser@example.com",
        hashed_password="Hashedpassword1!",
        confirmed=False,
        role="user",
        avatar="http://gravatar.com/avatar",
    )
    mock_repository.create_user.return_value = created_user

    # Mock Gravatar
    with patch("src.services.users.Gravatar") as mock_gravatar:
        mock_gravatar.return_value.get_image.return_value = "http://gravatar.com/avatar"

        # Call method
        result = await user_service.create_user(user_data)

        # Assertions
        assert result == created_user
        mock_gravatar.assert_called_once_with("newuser@example.com")
        mock_repository.create_user.assert_awaited_once_with(
            user_data, "http://gravatar.com/avatar"
        )


@pytest.mark.asyncio
async def test_get_user_by_id(user_service, mock_repository, test_user):
    """
    Test retrieving a user by their ID.
    """
    # Setup mock
    mock_repository.get_user_by_id.return_value = test_user

    # Call method
    result = await user_service.get_user_by_id(user_id=1)

    # Assertions
    assert result == test_user
    mock_repository.get_user_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_user_by_username(user_service, mock_repository, test_user):
    """
    Test retrieving a user by their username.
    """
    # Setup mock
    mock_repository.get_user_by_username.return_value = test_user

    # Call method
    result = await user_service.get_user_by_username(username="testuser")

    # Assertions
    assert result == test_user
    mock_repository.get_user_by_username.assert_awaited_once_with("testuser")


@pytest.mark.asyncio
async def test_get_user_by_email(user_service, mock_repository, test_user):
    """
    Test retrieving a user by their email.
    """
    # Setup mock
    mock_repository.get_user_by_email.return_value = test_user

    # Call method
    result = await user_service.get_user_by_email(email="testuser@example.com")

    # Assertions
    assert result == test_user
    mock_repository.get_user_by_email.assert_awaited_once_with("testuser@example.com")


@pytest.mark.asyncio
async def test_confirmed_email(user_service, mock_repository):
    """
    Test confirming a user's email.
    """
    # Call method
    await user_service.confirmed_email(email="testuser@example.com")

    # Assertions
    mock_repository.confirmed_email.assert_awaited_once_with("testuser@example.com")


@pytest.mark.asyncio
async def test_update_avatar_url(user_service, mock_repository, test_user):
    """
    Test updating a user's avatar URL.
    """
    # Setup mock
    mock_repository.update_avatar_url.return_value = test_user

    # Call method
    result = await user_service.update_avatar_url(
        email="testuser@example.com", url="http://new-avatar.com"
    )

    # Assertions
    assert result == test_user
    mock_repository.update_avatar_url.assert_awaited_once_with(
        "testuser@example.com", "http://new-avatar.com"
    )


@pytest.mark.asyncio
async def test_reset_password(user_service, mock_repository):
    """
    Test resetting a user's password.
    """
    # Call method
    await user_service.reset_password(
        email="testuser@example.com", hashed_password="newHashedpassword1!"
    )

    # Assertions
    mock_repository.reset_password.assert_awaited_once_with(
        "testuser@example.com", "newHashedpassword1!"
    )
