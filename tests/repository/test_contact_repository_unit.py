import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date
from src.repository.contacts import ContactRepository
from src.database.models import Contact, User
from src.schemas import ContactModel
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_session():
    """
    Fixture to create a mock AsyncSession.
    """
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def contact_repository(mock_session):
    """
    Fixture to create a ContactRepository with a mock session.
    """
    return ContactRepository(mock_session)


@pytest.fixture
def user():
    """
    Fixture to create a test user.
    """
    return User(id=1, username="testuser", email="testuser@example.com")


@pytest.mark.asyncio
async def test_get_contacts(contact_repository, mock_session, user):
    """
    Test retrieving a list of contacts for a user.
    """
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Contact(
            id=1,
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            user_id=user.id,
        )
    ]
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    contacts = await contact_repository.get_contacts(skip=0, limit=10, user=user)

    # Assertions
    assert len(contacts) == 1
    assert contacts[0].first_name == "John"
    assert contacts[0].email == "johndoe@example.com"


@pytest.mark.asyncio
async def test_get_contact_by_id(contact_repository, mock_session, user):
    """
    Test retrieving a contact by its ID.
    """
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        user_id=user.id,
    )
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    contact = await contact_repository.get_contact_by_id(contact_id=1, user=user)

    # Assertions
    assert contact is not None
    assert contact.first_name == "John"
    assert contact.email == "johndoe@example.com"


@pytest.mark.asyncio
async def test_create_contact(contact_repository, mock_session, user):
    """
    Test creating a new contact.
    """
    # Setup
    contact_data = ContactModel(
        first_name="Jane",
        last_name="Smith",
        email="janesmith@example.com",
        phone="+9876543210",
        birthday=date(1995, 5, 15),
    )

    # Setup mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Contact(
        id=1,
        first_name="Jane",
        last_name="Smith",
        email="janesmith@example.com",
        phone="+9876543210",
        birthday=date(1995, 5, 15),
        user_id=user.id,
    )
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call the actual method
    result = await contact_repository.create_contact(body=contact_data, user=user)

    # Assertions
    assert isinstance(result, Contact)
    assert result.first_name == "Jane"
    assert result.email == "janesmith@example.com"
    assert result.user_id == user.id
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_contact(contact_repository, mock_session, user):
    """
    Test updating an existing contact.
    """
    # Setup
    contact_data = ContactModel(
        first_name="Johnny",
        last_name="Doe",
        email="johnnydoe@example.com",
        phone="+1234567890",
        birthday=date(1990, 1, 1),
    )
    existing_contact = Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        user_id=user.id,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contact_repository.update_contact(
        contact_id=1, body=contact_data, user=user
    )

    # Assertions
    assert result is not None
    assert result.first_name == "Johnny"
    assert result.email == "johnnydoe@example.com"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(existing_contact)


@pytest.mark.asyncio
async def test_remove_contact(contact_repository, mock_session, user):
    """
    Test removing a contact by its ID.
    """
    # Setup
    existing_contact = Contact(
        id=1,
        first_name="John",
        last_name="Doe",
        email="johndoe@example.com",
        user_id=user.id,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contact_repository.remove_contact(contact_id=1, user=user)

    # Assertions
    assert result is not None
    assert result.first_name == "John"
    mock_session.delete.assert_awaited_once_with(existing_contact)
    mock_session.commit.assert_awaited_once()
