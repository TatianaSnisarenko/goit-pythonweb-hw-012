import pytest
from sqlalchemy import select
from src.database.models import Contact
from tests.conftest import TestingSessionLocal

base_contact_data = {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "1234567890",
    "birthday": "1990-01-01",
    "description": "Friend from work",
}


@pytest.mark.asyncio
async def test_create_contact(client, get_token):
    """
    Test creating a new contact.
    """
    contact_data = {**base_contact_data, "email": "create_contact@example.com"}
    headers = {"Authorization": f"Bearer {get_token}"}
    response = client.post("api/contacts/", json=contact_data, headers=headers)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["first_name"] == contact_data["first_name"]
    assert data["last_name"] == contact_data["last_name"]
    assert data["email"] == contact_data["email"]


@pytest.mark.asyncio
async def test_get_contact(client, get_token):
    """
    Test retrieving a contact by ID.
    """
    contact_data = {**base_contact_data, "email": "get_contact@example.com"}
    headers = {"Authorization": f"Bearer {get_token}"}

    # Create a contact
    response = client.post("api/contacts/", json=contact_data, headers=headers)
    assert response.status_code == 201, response.text
    contact_id = response.json()["id"]

    # Retrieve the contact
    response = client.get(f"api/contacts/{contact_id}", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == contact_id
    assert data["first_name"] == contact_data["first_name"]


@pytest.mark.asyncio
async def test_update_contact(client, get_token):
    """
    Test updating an existing contact.
    """
    contact_data = {**base_contact_data, "email": "update_contact@example.com"}
    headers = {"Authorization": f"Bearer {get_token}"}

    # Create a contact
    response = client.post("api/contacts/", json=contact_data, headers=headers)
    assert response.status_code == 201, response.text
    contact_id = response.json()["id"]

    # Update the contact
    updated_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "updated_contact@example.com",
        "phone": "0987654321",
        "birthday": "1995-05-06",
    }
    response = client.put(
        f"api/contacts/{contact_id}", json=updated_data, headers=headers
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == updated_data["first_name"]
    assert data["last_name"] == updated_data["last_name"]


@pytest.mark.asyncio
async def test_delete_contact(client, get_token):
    """
    Test deleting a contact.
    """
    contact_data = {**base_contact_data, "email": "delete_contact@example.com"}
    headers = {"Authorization": f"Bearer {get_token}"}

    # Create a contact
    response = client.post("api/contacts/", json=contact_data, headers=headers)
    assert response.status_code == 201, response.text
    contact_id = response.json()["id"]

    # Delete the contact
    response = client.delete(f"api/contacts/{contact_id}", headers=headers)
    assert response.status_code == 200, response.text

    # Verify the contact no longer exists
    response = client.get(f"api/contacts/{contact_id}", headers=headers)
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["message"] == "Contact not found"
