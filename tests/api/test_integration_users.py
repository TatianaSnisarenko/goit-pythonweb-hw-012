import pytest


@pytest.mark.asyncio
async def test_get_current_user(client, get_token_confirmed, test_user_confirmed):
    """
    Test retrieving the current authenticated user's details.
    """
    headers = {"Authorization": f"Bearer {get_token_confirmed}"}
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "username" in data
    assert "email" in data
    assert data["username"] == test_user_confirmed["username"]
    assert data["email"] == test_user_confirmed["email"]


@pytest.mark.asyncio
async def test_update_avatar_as_admin(client, get_admin_token, mocker):
    """
    Test updating the avatar of the current user (admin role required).
    """
    # Mock the UploadFileService to avoid real Cloudinary calls
    mock_upload_file_service = mocker.patch(
        "src.services.upload_file.UploadFileService.upload_file",
        return_value="https://mocked-cloudinary-url.com/avatar.jpg",
    )

    headers = {"Authorization": f"Bearer {get_admin_token}"}
    files = {"file": ("avatar.jpg", b"fake_image_data", "image/jpeg")}

    response = client.patch("/api/users/avatar", headers=headers, files=files)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "avatar" in data
    assert data["avatar"] == "https://mocked-cloudinary-url.com/avatar.jpg"

    # Ensure the mock was called with the correct arguments
    mock_upload_file_service.assert_called_once_with(
        mocker.ANY,  # The file object
        "adminuser",  # The username
    )


@pytest.mark.asyncio
async def test_update_avatar_as_non_admin(client, get_token_confirmed):
    """
    Test that a non-admin user cannot update their avatar.
    """
    headers = {"Authorization": f"Bearer {get_token_confirmed}"}
    files = {"file": ("avatar.jpg", b"fake_image_data", "image/jpeg")}

    response = client.patch("/api/users/avatar", headers=headers, files=files)
    assert response.status_code == 403, response.text
    data = response.json()
    assert data["message"] == "You are not authorized to perform this action."
