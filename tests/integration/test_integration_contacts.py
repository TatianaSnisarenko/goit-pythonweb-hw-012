from datetime import datetime, timedelta
import pytest

from src.services.auth import create_access_token
from tests.test_utils import create_contact

base_contact_data = {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "1234567890",
    "birthday": "1990-01-01",
    "description": "Friend from work",
}


@pytest.mark.asyncio
async def test_create_contact(client, get_token_confirmed):
    """
    Test creating a new contact.
    """
    contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "1234567890",
        "birthday": "1990-01-01",
        "description": "Friend from work",
        "email": "create_contact@example.com",
    }
    headers = {"Authorization": f"Bearer {get_token_confirmed}"}
    response = client.post("api/contacts/", json=contact_data, headers=headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["first_name"] == contact_data["first_name"]
    assert data["last_name"] == contact_data["last_name"]
    assert data["email"] == contact_data["email"]


@pytest.mark.asyncio
async def test_create_contact_user_not_authenticated(client):
    """
    Test creating a new contact.
    """
    contact_data = {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "1234567890",
        "birthday": "1990-01-01",
        "description": "Friend from work",
        "email": "create_contact@example.com",
    }
    response = client.post("api/contacts/", json=contact_data)
    assert response.status_code == 401, response.text
    data = response.json()
    data["message"] = "Not authenticated"


@pytest.mark.asyncio
async def test_get_contact_by_id(client, get_token_confirmed, test_user_confirmed):
    """
    Test retrieving a contact by ID.
    """
    contact_data = await create_contact(test_user_confirmed["email"])
    assert contact_data is not None
    headers = {"Authorization": f"Bearer {get_token_confirmed}"}

    # Retrieve the contact
    response = client.get(f"api/contacts/{contact_data.id}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == contact_data.id
    assert data["first_name"] == contact_data.first_name
    assert data["last_name"] == contact_data.last_name
    assert data["email"] == contact_data.email
    assert data["phone"] == contact_data.phone
    assert data["birthday"] == contact_data.birthday.isoformat()


@pytest.mark.asyncio
async def test_get_contact_by_id_not_authenticated(client):
    """
    Test retrieving a contact by ID.
    """
    response = client.get(f"api/contacts/1")
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["message"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_contact(client, get_token_confirmed, test_user_confirmed):
    """
    Test updating an existing contact.
    """
    contact_data = await create_contact(test_user_confirmed["email"])
    assert contact_data is not None
    headers = {"Authorization": f"Bearer {get_token_confirmed}"}

    # Update the contact
    updated_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "updated_contact@example.com",
        "phone": "0987654321",
        "birthday": "1995-05-06",
    }
    response = client.put(
        f"api/contacts/{contact_data.id}", json=updated_data, headers=headers
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == updated_data["first_name"]
    assert data["last_name"] == updated_data["last_name"]
    assert data["email"] == updated_data["email"]
    assert data["phone"] == updated_data["phone"]
    assert data["birthday"] == updated_data["birthday"]


@pytest.mark.asyncio
async def test_update_contact_not_authenticated(client):
    """
    Test updating an existing contact.
    """
    updated_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "updated_contact@example.com",
        "phone": "0987654321",
        "birthday": "1995-05-06",
    }
    response = client.put(f"api/contacts/{1}", json=updated_data)
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["message"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_contact(client, get_token_confirmed, test_user_confirmed):
    """
    Test deleting a contact.
    """
    contact_data = await create_contact(test_user_confirmed["email"])
    assert contact_data is not None
    headers = {"Authorization": f"Bearer {get_token_confirmed}"}

    # Delete the contact
    response = client.delete(f"api/contacts/{contact_data.id}", headers=headers)
    assert response.status_code == 200, response.text

    # Verify the contact no longer exists
    response = client.get(f"api/contacts/{contact_data.id}", headers=headers)
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["message"] == "Contact not found"


@pytest.mark.asyncio
async def test_delete_contact_not_authenticated(client):
    """
    Test deleting a contact.
    """
    response = client.delete(f"api/contacts/{1}")
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["message"] == "Not authenticated"


@pytest.mark.asyncio
async def test_read_contacts(client, get_token_confirmed, test_user_confirmed):
    """
    Test retrieving a list of contacts with pagination.
    """
    # Create multiple contacts for the test user
    for _ in range(3):
        await create_contact(test_user_confirmed["email"])

    headers = {"Authorization": f"Bearer {get_token_confirmed}"}

    # Retrieve the list of contacts
    response = client.get("/api/contacts/?skip=0&limit=10", headers=headers)
    assert response.status_code == 200, response.text

    # Parse the response data
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Ensure 3 contacts are returned

    # Validate the structure of the returned contacts
    for contact in data:
        assert "id" in contact
        assert "first_name" in contact
        assert "last_name" in contact
        assert "email" in contact
        assert "phone" in contact
        assert "birthday" in contact


@pytest.mark.asyncio
async def test_read_contacts_not_authenticated(client):
    """
    Test retrieving a list of contacts with pagination.
    """
    response = client.get("/api/contacts/?skip=0&limit=10")
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["message"] == "Not authenticated"


@pytest.mark.asyncio
async def test_search_contacts_by_first_name(
    client, get_token_confirmed, test_user_confirmed
):
    """
    Test searching contacts by first name.
    """
    # Create contacts for the test user
    await create_contact(test_user_confirmed["email"])
    await create_contact(test_user_confirmed["email"])

    headers = {"Authorization": f"Bearer {get_token_confirmed}"}

    # Search contacts by first name
    response = client.get("/api/contacts/search/?first_name=John", headers=headers)
    assert response.status_code == 200, response.text

    # Parse the response data
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Ensure at least one contact is returned

    # Validate the structure of the returned contacts
    for contact in data:
        assert "id" in contact
        assert "first_name" in contact
        assert "last_name" in contact
        assert "email" in contact
        assert "phone" in contact
        assert "birthday" in contact
        assert contact["first_name"] == "John"


@pytest.mark.asyncio
async def test_search_contacts_by_last_name(
    client, get_token_confirmed, test_user_confirmed
):
    """
    Test searching contacts by last name.
    """
    # Create contacts for the test user
    await create_contact(test_user_confirmed["email"])

    headers = {"Authorization": f"Bearer {get_token_confirmed}"}

    # Search contacts by last name
    response = client.get("/api/contacts/search/?last_name=Doe", headers=headers)
    assert response.status_code == 200, response.text

    # Parse the response data
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0  # Ensure at least one contact is returned

    # Validate the structure of the returned contacts
    for contact in data:
        assert "id" in contact
        assert "first_name" in contact
        assert "last_name" in contact
        assert "email" in contact
        assert "phone" in contact
        assert "birthday" in contact
        assert contact["last_name"] == "Doe"


@pytest.mark.asyncio
async def test_search_contacts_by_email(
    client, get_token_confirmed, test_user_confirmed
):
    """
    Test searching contacts by email.
    """
    # Create a contact for the test user
    contact_data = await create_contact(test_user_confirmed["email"])

    headers = {"Authorization": f"Bearer {get_token_confirmed}"}

    # Search contacts by email
    response = client.get(
        f"/api/contacts/search/?email={contact_data.email}", headers=headers
    )
    assert response.status_code == 200, response.text

    # Parse the response data
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1  # Ensure exactly one contact is returned

    # Validate the structure of the returned contact
    contact = data[0]
    assert contact["id"] == contact_data.id
    assert contact["first_name"] == contact_data.first_name
    assert contact["last_name"] == contact_data.last_name
    assert contact["email"] == contact_data.email
    assert contact["phone"] == contact_data.phone
    assert contact["birthday"] == contact_data.birthday.isoformat()


@pytest.mark.asyncio
async def test_search_contacts_by_first_name_not_authenticated(client):
    """
    Test searching contacts by first name.
    """
    response = client.get("/api/contacts/search/?first_name=John")
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["message"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(client, get_token_confirmed, test_user_confirmed):
    """
    Test retrieving contacts with upcoming birthdays within the next 7 days.
    """
    # Create contacts with birthdays today and within the next 7 days
    today = datetime.now().date()
    birthday_today = today
    birthday_in_3_days = today + timedelta(days=3)
    birthday_in_7_days = today + timedelta(days=7)

    await create_contact(test_user_confirmed["email"], birthday=birthday_today)
    await create_contact(test_user_confirmed["email"], birthday=birthday_in_3_days)
    await create_contact(test_user_confirmed["email"], birthday=birthday_in_7_days)

    # Create a contact with a birthday outside the 7-day range
    birthday_outside_range = today + timedelta(days=10)
    await create_contact(test_user_confirmed["email"], birthday=birthday_outside_range)

    headers = {"Authorization": f"Bearer {get_token_confirmed}"}

    # Retrieve contacts with upcoming birthdays
    response = client.get("/api/contacts/birthdays/?days=7", headers=headers)
    assert response.status_code == 200, response.text

    # Parse the response data
    data = response.json()
    assert isinstance(data, list)

    # Validate that only contacts with birthdays within the next 7 days are returned
    valid_birthdays = [
        (datetime.now().date() + timedelta(days=i)).isoformat() for i in range(7)
    ]

    for contact in data:
        print("My print        ")

        print(valid_birthdays)
        assert contact["birthday"] in valid_birthdays


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(client, get_token_confirmed, test_user_confirmed):
    """
    Test retrieving contacts with upcoming birthdays within the next 7 days.
    """
    # Create contacts with birthdays today and within the next 7 days
    today = datetime.now().date()
    birthday_today = today
    birthday_in_3_days = today + timedelta(days=3)
    birthday_in_7_days = today + timedelta(days=7)

    await create_contact(test_user_confirmed["email"], birthday=birthday_today)
    await create_contact(test_user_confirmed["email"], birthday=birthday_in_3_days)
    await create_contact(test_user_confirmed["email"], birthday=birthday_in_7_days)

    # Create a contact with a birthday outside the 7-day range
    birthday_outside_range = today + timedelta(days=10)
    await create_contact(test_user_confirmed["email"], birthday=birthday_outside_range)

    headers = {"Authorization": f"Bearer {get_token_confirmed}"}

    # Retrieve contacts with upcoming birthdays
    response = client.get("/api/contacts/birthdays/?days=7", headers=headers)
    assert response.status_code == 200, response.text

    # Parse the response data
    data = response.json()
    assert isinstance(data, list)

    # Generate a list of valid birthdays for the next 7 days
    valid_birthdays = [(today + timedelta(days=i)).isoformat() for i in range(8)]

    # Validate that only contacts with birthdays within the next 7 days are returned
    for contact in data:
        assert contact["birthday"] in valid_birthdays


@pytest.mark.asyncio
async def test_get_upcoming_birthdays_not_authenticated(client):
    """
    Test retrieving contacts with upcoming birthdays when no contacts match the criteria.
    """
    response = client.get("/api/contacts/birthdays/?days=7")
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["message"] == "Not authenticated"
