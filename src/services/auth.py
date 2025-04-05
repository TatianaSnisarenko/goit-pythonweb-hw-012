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
from src.database.models import RefreshToken
from src.services.refresh_tokens import RefreshTokenService
from src.schemas import TokenDto
from src.database.models import User
from src.utils.utils import parse_datetime_fields, to_dict


class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_token(
    data: dict, expires_delta: timedelta, token_type: Literal["access", "refresh"]
) -> TokenDto:
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return TokenDto(token=encoded_jwt, expires_at=expire, created_at=now)


async def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
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


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    cache: Redis = Depends(get_cache),
) -> User:
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


def create_email_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str):
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Неправильний токен для перевірки електронної пошти",
        )


async def verify_refresh_token(refresh_token: str, db: AsyncSession):
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
