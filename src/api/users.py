from fastapi import APIRouter, Depends, Request
from src.schemas import User
from src.services.auth import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.conf.config import settings
from src.services.users import UserService
from src.services.upload_file import UploadFileService

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=User)
@limiter.limit("5/minute")
async def me(request: Request, user: User = Depends(get_current_user)):
    """
    Get details of the currently authenticated user.
    - Requires a valid access token in the `Authorization` header.
    - Requests are limited up to 5 per minute.
    """
    return user


@router.patch("/avatar", response_model=User)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the avatar of the authenticated user by uploading a new image file.
    """
    avatar_url = UploadFileService(
        settings.CLOUDINARY_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET,
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user = await user_service.update_avatar_url(user.email, avatar_url)

    return user
