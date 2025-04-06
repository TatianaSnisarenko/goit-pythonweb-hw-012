import pytest
from datetime import datetime
from src.utils.utils import parse_datetime_fields, to_dict
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime


Base = declarative_base()


@pytest.fixture
def mock_model_class():
    """
    Fixture to provide a mock SQLAlchemy model class.
    """

    class MockModel(Base):
        __tablename__ = "mock_model"
        id = Column(Integer, primary_key=True)
        name = Column(String)
        created_at = Column(DateTime)

    return MockModel


def test_parse_datetime_fields():
    """
    Test the `parse_datetime_fields` function.
    """
    # Setup
    data = {
        "name": "John Doe",
        "created_at": "2025-04-06T12:00:00",
        "updated_at": "invalid_datetime",
    }
    datetime_fields = ["created_at", "updated_at"]

    # Call the function
    result = parse_datetime_fields(data, datetime_fields)

    # Assertions
    assert result["created_at"] == datetime(2025, 4, 6, 12, 0, 0)
    assert (
        result["updated_at"] == "invalid_datetime"
    )  # Invalid datetime remains unchanged
    assert result["name"] == "John Doe"


def test_to_dict(mock_model_class):
    """
    Test the `to_dict` function.
    """
    # Setup
    mock_model = mock_model_class(
        id=1,
        name="John Doe",
        created_at=datetime(2025, 4, 6, 12, 0, 0),
    )

    # Call the function
    result = to_dict(mock_model)

    # Assertions
    assert result["id"] == 1
    assert result["name"] == "John Doe"
    assert result["created_at"] == "2025-04-06T12:00:00"
