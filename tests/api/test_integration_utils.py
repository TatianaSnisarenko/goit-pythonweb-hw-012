import pytest

from src.database.db import get_db
from main import app


@pytest.mark.asyncio
async def test_healthchecker_success(client):
    """
    Test the /healthchecker endpoint when the database connection is successful.
    """
    response = client.get("api/healthchecker")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "message" in data
    assert data["message"] == "Welcome to ContactAPI!"


@pytest.mark.asyncio
async def test_healthchecker_database_error(client):
    """
    Test the /healthchecker endpoint when the database connection fails.
    """

    async def failing_get_db():
        return None

    app.dependency_overrides[get_db] = failing_get_db

    response = client.get("/api/healthchecker")
    assert response.status_code == 500, response.text
    data = response.json()
    assert "message" in data
    assert data["message"] == "Error connecting to the database"

    app.dependency_overrides.pop(get_db, None)
