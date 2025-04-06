from datetime import datetime, timedelta, UTC
import json
from typing import Optional, Literal

from redis.asyncio import Redis
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from src.cache.cache import get_cache
from src.conf.config import settings
from src.database.db import get_db
from src.services.users import UserService
from src.database.models import RefreshToken, UserRole
from src.services.refresh_tokens import RefreshTokenService
from src.schemas import TokenDto
from src.database.models import User
from src.utils.utils import parse_datetime_fields, to_dict

"""
Authentication and authorization services module.

This module provides functionality for managing authentication and authorization 
in the application. It includes password hashing, token creation, user validation, 
and role-based access control.

Classes:
    Hash: A utility class for password hashing and verification.

Functions:
    create_token: Creates a JWT token with a specified expiration time and type.
    create_access_token: Creates an access token for a user.
    create_refresh_token: Creates a refresh token for a user and stores it in the database.
    update_refresh_token: Updates an existing refresh token with a new one.
    get_current_user: Retrieves the currently authenticated user from the token.
    get_current_admin_user: Retrieves the currently authenticated admin user.
    create_email_token: Creates a token for email verification.
    get_email_from_token: Extracts the email from a token.
    verify_refresh_token: Verifies the validity of a refresh token.
"""


class Hash:
    """
    A utility class for password hashing and verification.

    Methods:
        verify_password: Verifies a plain password against a hashed password.
        get_password_hash: Hashes a plain password using bcrypt.
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies a plain password against a hashed password.

        Args:
            plain_password (str): The plain text password to verify.
            hashed_password (str): The hashed password to compare against.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Hashes a plain password using bcrypt.

        Args:
            password (str): The plain text password to hash.

        Returns:
            str: The hashed password.
        """
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_token(
    data: dict, expires_delta: timedelta, token_type: Literal["access", "refresh"]
) -> TokenDto:
    """
    Creates a JWT token with a specified expiration time and type.

    Args:
        data (dict): The payload data to encode in the token.
        expires_delta (timedelta): The duration until the token expires.
        token_type (Literal["access", "refresh"]): The type of the token.

    Returns:
        TokenDto: The created token with metadata.
    """
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return TokenDto(token=encoded_jwt, expires_at=expire, created_at=now)


async def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """
    Creates an access token for a user.

    Args:
        data (dict): The payload data to encode in the token.
        expires_delta (Optional[int]): The duration until the token expires in seconds.

    Returns:
        str: The created access token.
    """
    if expires_delta:
        access_token = create_token(data, expires_delta, "access")
    else:
        access_token = create_token(
            data, timedelta(seconds=settings.ACCESS_TOKEN_EXPIRATION_SECONDS), "access"
        )
    return access_token.token


async def create_refresh_token(
    data: dict, user_id: int, db: AsyncSession, expires_delta: Optional[float] = None
) -> RefreshToken:
    """
    Creates a refresh token for a user and stores it in the database.

    Args:
        data (dict): The payload data to encode in the token.
        user_id (int): The ID of the user for whom the token is created.
        db (AsyncSession): The database session.
        expires_delta (Optional[float]): The duration until the token expires in minutes.

    Returns:
        RefreshToken: The created refresh token object.
    """
    if expires_delta:
        refresh_token = create_token(data, expires_delta, "refresh")
    else:
        refresh_token = create_token(
            data,
            timedelta(minutes=settings.REFRESH_TOKEN_EXPIRATION_SECONDS),
            "refresh",
        )
    refresh_token_service = RefreshTokenService(db)
    refresh_token_obj = await refresh_token_service.create_refresh_token(
        refresh_token, user_id
    )
    return refresh_token_obj


async def update_refresh_token(
    data: dict,
    old_refresh_token: str,
    user_id: int,
    db: AsyncSession,
    expires_delta: Optional[float] = None,
) -> RefreshToken:
    """
    Updates an existing refresh token with a new one.

    Args:
        data (dict): The payload data to encode in the token.
        old_refresh_token (str): The old refresh token to replace.
        user_id (int): The ID of the user associated with the token.
        db (AsyncSession): The database session.
        expires_delta (Optional[float]): The duration until the token expires in minutes.

    Returns:
        RefreshToken: The updated refresh token object.
    """
    if expires_delta:
        refresh_token = create_token(data, expires_delta, "refresh")
    else:
        refresh_token = create_token(
            data,
            timedelta(minutes=settings.REFRESH_TOKEN_EXPIRATION_SECONDS),
            "refresh",
        )
    refresh_token_service = RefreshTokenService(db)
    refresh_token_obj = await refresh_token_service.update_refresh_token(
        old_refresh_token, refresh_token, user_id
    )
    return refresh_token_obj


async def get_current_admin_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    cache: Redis = Depends(get_cache),
) -> User:
    """
    Retrieves the currently authenticated admin user.

    Args:
        token (str): The JWT token from the request.
        db (AsyncSession): The database session.
        cache (Redis): The Redis cache instance.

    Returns:
        User: The authenticated admin user.

    Raises:
        HTTPException: If the user is not an admin or the token is invalid.
    """
    user = await get_current_user(token, db, cache)
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to perform this action.",
        )
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    cache: Redis = Depends(get_cache),
) -> User:
    """
    Retrieves the currently authenticated user from the token.

    Args:
        token (str): The JWT token from the request.
        db (AsyncSession): The database session.
        cache (Redis): The Redis cache instance.

    Returns:
        User: The authenticated user.

    Raises:
        HTTPException: If the token is invalid or the user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    cached_user = await cache.get(f"user:{token}")
    if cached_user:
        user_data = parse_datetime_fields(json.loads(cached_user), ["created_at"])
        user = User(**user_data)
        user = await db.merge(user)
        return user

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type")
        if username is None or token_type != "access":
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception

    await cache.set(f"user:{token}", json.dumps(to_dict(user)), ex=3600)
    return user


def create_email_token(data: dict) -> str:
    """
    Creates a token for email verification.

    Args:
        data (dict): The payload data to encode in the token.

    Returns:
        str: The created email verification token.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str) -> str:
    """
    Extracts the email from a token.

    Args:
        token (str): The JWT token containing the email.

    Returns:
        str: The extracted email.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Not valid token",
        )


async def verify_refresh_token(refresh_token: str, db: AsyncSession) -> Optional[User]:
    """
    Verifies the validity of a refresh token.

    Args:
        refresh_token (str): The refresh token to verify.
        db (AsyncSession): The database session.

    Returns:
        Optional[User]: The user associated with the token if valid, otherwise None.
    """
    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        token_type: str = payload.get("token_type")
        if username is None or token_type != "refresh":
            return None
        user_service = UserService(db)
        user = await user_service.get_user_by_username_and_by_refresh_token(
            username, refresh_token
        )
        return user
    except JWTError:
        return None
