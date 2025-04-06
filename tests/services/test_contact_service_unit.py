import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date, timedelta
from src.services.contacts import ContactService
from src.schemas import ContactModel, User
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def mock_repository():
    """
    Fixture to create a mock ContactRepository.
    """
    return AsyncMock()


@pytest.fixture
def contact_service(mock_repository):
    """
    Fixture to create a ContactService with a mocked repository.
    """
    service = ContactService(db=None)
    service.contact_repository = mock_repository
    return service


@pytest.fixture
def test_user():
    """
    Fixture to create a test user.
    """
    return User(
        id=1, username="testuser", email="testuser@example.com", role="user", avatar=""
    )


@pytest.fixture
def test_contact():
    """
    Fixture to create a test contact.
    """
    return ContactModel(
        id=1,
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        phone="+1234567890",
        birthday=date(1990, 1, 1),
    )


@pytest.mark.asyncio
async def test_create_contact(
    contact_service, mock_repository, test_user, test_contact
):
    """
    Test creating a new contact.
    """
    # Setup
    mock_repository.create_contact.return_value = test_contact

    # Call method
    result = await contact_service.create_contact(test_contact, test_user)

    # Assertions
    assert result == test_contact
    mock_repository.create_contact.assert_awaited_once_with(test_contact, test_user)


@pytest.mark.asyncio
async def test_create_contact_integrity_error(
    contact_service, mock_repository, test_user, test_contact
):
    """
    Test creating a contact with an IntegrityError.
    """
    # Setup
    mock_repository.create_contact.side_effect = IntegrityError(
        "Mock error", None, None
    )

    # Call method and assert exception
    with pytest.raises(Exception) as exc_info:
        await contact_service.create_contact(test_contact, test_user)

    assert "Database integrity error" in str(exc_info.value)
    mock_repository.create_contact.assert_awaited_once_with(test_contact, test_user)


@pytest.mark.asyncio
async def test_get_contacts(contact_service, mock_repository, test_user, test_contact):
    """
    Test retrieving a list of contacts.
    """
    # Setup
    mock_repository.get_contacts.return_value = [test_contact]

    # Call method
    result = await contact_service.get_contacts(skip=0, limit=10, user=test_user)

    # Assertions
    assert result == [test_contact]
    mock_repository.get_contacts.assert_awaited_once_with(0, 10, test_user)


@pytest.mark.asyncio
async def test_get_contact(contact_service, mock_repository, test_user, test_contact):
    """
    Test retrieving a specific contact by ID.
    """
    # Setup
    mock_repository.get_contact_by_id.return_value = test_contact

    # Call method
    result = await contact_service.get_contact(contact_id=1, user=test_user)

    # Assertions
    assert result == test_contact
    mock_repository.get_contact_by_id.assert_awaited_once_with(1, test_user)


@pytest.mark.asyncio
async def test_update_contact(
    contact_service, mock_repository, test_user, test_contact
):
    """
    Test updating a contact.
    """
    # Setup
    mock_repository.update_contact.return_value = test_contact

    # Call method
    result = await contact_service.update_contact(
        contact_id=1, body=test_contact, user=test_user
    )

    # Assertions
    assert result == test_contact
    mock_repository.update_contact.assert_awaited_once_with(1, test_contact, test_user)


@pytest.mark.asyncio
async def test_remove_contact(
    contact_service, mock_repository, test_user, test_contact
):
    """
    Test removing a contact.
    """
    # Setup
    mock_repository.remove_contact.return_value = test_contact

    # Call method
    result = await contact_service.remove_contact(contact_id=1, user=test_user)

    # Assertions
    assert result == test_contact
    mock_repository.remove_contact.assert_awaited_once_with(1, test_user)


@pytest.mark.asyncio
async def test_search_contacts(
    contact_service, mock_repository, test_user, test_contact
):
    """
    Test searching for contacts.
    """
    # Setup
    mock_repository.search_contacts.return_value = [test_contact]

    # Call method
    result = await contact_service.search_contacts(
        skip=0, limit=10, first_name="John", last_name=None, email=None, user=test_user
    )

    # Assertions
    assert result == [test_contact]
    mock_repository.search_contacts.assert_awaited_once_with(
        0, 10, "John", None, None, test_user
    )


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(
    contact_service, mock_repository, test_user, test_contact
):
    """
    Test retrieving contacts with upcoming birthdays.
    """
    # Setup
    mock_repository.get_upcoming_birthdays.return_value = [test_contact]

    # Call method
    result = await contact_service.get_upcoming_birthdays(
        days=7, skip=0, limit=10, user=test_user
    )

    # Assertions
    assert result == [test_contact]
    today = date.today()
    next_date = today + timedelta(days=7)
    mock_repository.get_upcoming_birthdays.assert_awaited_once_with(
        today, next_date, 0, 10, test_user
    )
