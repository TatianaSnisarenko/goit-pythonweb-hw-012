from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.schemas import UpdateUserRoleRequest, User, UserWithRoleResponse
from src.services.auth import get_current_user, get_current_admin_user
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.conf.config import settings
from src.services.users import UserService
from src.services.upload_file import UploadFileService

"""
Users API module.

This module provides endpoints for managing user-related operations. It includes 
functionality for retrieving the current user's details and updating the user's avatar.

Routes:
    /users/me:
        - GET: Retrieve details of the currently authenticated user.
    /users/avatar:
        - PATCH: Update the avatar of the authenticated user by uploading a new image file.
    /users/{user_id}/role:
        - PATCH: Update the role of a user. Only accessible by admins.

Dependencies:
    - Database session (`AsyncSession`) is used for database operations.
    - Current user (`User`) is retrieved using authentication dependencies.
    - Cloudinary is used for storing and managing user avatars.

Exception Handling:
    - Raises `HTTPException` for unauthorized access or invalid data.
    - Limits requests to `/users/me` to 5 per minute using `Limiter`.
"""

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=User)
@limiter.limit("5/minute")
async def me(request: Request, user: User = Depends(get_current_user)) -> User:
    """
    Get details of the currently authenticated user.

    This endpoint retrieves the details of the user who is currently authenticated.
    Requires a valid access token in the `Authorization` header. Requests are limited
    to 5 per minute.

    Args:
        request (Request): The HTTP request object.
        user (User): The currently authenticated user.

    Returns:
        User: The details of the authenticated user.
    """
    return user


@router.patch("/avatar", response_model=User)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Update the avatar of the authenticated user by uploading a new image file.

    This endpoint allows the authenticated user to update their avatar by uploading
    a new image file. The image is uploaded to Cloudinary, and the avatar URL is updated
    in the user's profile.

    Args:
        file (UploadFile): The image file to upload as the new avatar.
        user (User): The currently authenticated user (must be an admin).
        db (AsyncSession): The database session.

    Returns:
        User: The updated user with the new avatar URL.
    """
    avatar_url = UploadFileService(
        settings.CLOUDINARY_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET,
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user = await user_service.update_avatar_url(user.email, avatar_url)

    return user


@router.patch("/{user_id}/role", response_model=UserWithRoleResponse)
async def update_user_role(
    user_id: int,
    role_request: UpdateUserRoleRequest,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserWithRoleResponse:
    """
    Update the role of a user. Only accessible by admins.

    Args:
        user_id (int): The ID of the user whose role is to be updated.
        role_request (UpdateUserRoleRequest): The new role for the user.
        admin_user (User): The currently authenticated admin user.
        db (AsyncSession): The database session.

    Returns:
        UserResponse: The updated user with the new role.

    Raises:
        HTTPException: If the user is not found.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user = await user_service.update_user_role(user_id, role_request.role)
    return user
