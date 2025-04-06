import pytest
from unittest.mock import patch, MagicMock
from fastapi import UploadFile
from src.services.upload_file import UploadFileService


@pytest.fixture
def mock_cloudinary_config():
    """
    Fixture to mock Cloudinary configuration.
    """
    with patch("cloudinary.config") as mock_config:
        yield mock_config


@pytest.fixture
def mock_cloudinary_uploader():
    """
    Fixture to mock Cloudinary uploader.
    """
    with patch("cloudinary.uploader.upload") as mock_uploader:
        yield mock_uploader


@pytest.fixture
def mock_cloudinary_image():
    """
    Fixture to mock CloudinaryImage.
    """
    with patch("cloudinary.CloudinaryImage") as mock_image:
        yield mock_image


@pytest.fixture
def test_file():
    """
    Fixture to create a mock UploadFile.
    """
    file_mock = MagicMock(spec=UploadFile)
    file_mock.file = MagicMock()
    return file_mock


@pytest.mark.asyncio
async def test_upload_file(
    mock_cloudinary_config, mock_cloudinary_uploader, mock_cloudinary_image, test_file
):
    """
    Test uploading a file to Cloudinary.
    """
    # Setup
    mock_cloudinary_uploader.return_value = {"version": "12345"}
    mock_cloudinary_image.return_value.build_url.return_value = "http://mocked-url.com"

    # Call the method
    service = UploadFileService(
        cloud_name="mock_cloud", api_key="mock_key", api_secret="mock_secret"
    )
    result = service.upload_file(test_file, username="testuser")

    # Assertions
    mock_cloudinary_config.assert_called_once_with(
        cloud_name="mock_cloud",
        api_key="mock_key",
        api_secret="mock_secret",
        secure=True,
    )
    mock_cloudinary_uploader.assert_called_once_with(
        test_file.file, public_id="RestApp/testuser", overwrite=True
    )
    mock_cloudinary_image.assert_called_once_with("RestApp/testuser")
    mock_cloudinary_image.return_value.build_url.assert_called_once_with(
        width=250, height=250, crop="fill", version="12345"
    )
    assert result == "http://mocked-url.com"
