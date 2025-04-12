import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.cache.cache import get_cache
from main import app
from src.database.models import Base, User
from src.database.db import get_db
from src.services.auth import create_access_token, Hash

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

test_user_confirmed_obj = {
    "username": "deadpool",
    "email": "deadpool@example.com",
    "password": "Password123!",
    "role": "user",
}

test_user_not_confirmed_obj = {
    "username": "notconfirmed",
    "email": "notconfirmed@example.com",
    "password": "NotPassword123!",
    "role": "user",
}

test_user_admin_obj = {
    "username": "adminuser",
    "email": "admin@example.com",
    "password": "AdminPassword123!",
    "role": "admin",
}


@pytest.fixture(scope="module")
def test_user_confirmed():
    """
    Fixture to provide test_user_confirmed data.
    """
    return test_user_confirmed_obj


@pytest.fixture(scope="module")
def test_user_not_confirmed():
    """
    Fixture to provide test_user_not_confirmed data.
    """
    return test_user_not_confirmed_obj


@pytest.fixture(scope="module")
def test_user_admin():
    """
    Fixture to provide admin_user data.
    """
    return test_user_admin_obj


async def create_user(session, user_data, confirmed=True):
    """
    Helper function to create a user in the database.

    Args:
        session: The database session.
        user_data: Dictionary with user data.
        confirmed: Whether the user's email is confirmed.

    Returns:
        None
    """
    hashed_password = Hash().get_password_hash(user_data["password"])
    user = User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=hashed_password,
        role=user_data["role"],
        confirmed=confirmed,
        avatar="<https://twitter.com/gravatar>",
    )
    session.add(user)
    await session.commit()


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            # Create users
            await create_user(session, test_user_confirmed_obj, confirmed=True)
            await create_user(session, test_user_admin_obj, confirmed=True)
            await create_user(session, test_user_not_confirmed_obj, confirmed=False)

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client(mock_redis):
    # Dependency override

    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception as err:
                await session.rollback()
                raise

    async def override_get_cache():
        return mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache] = override_get_cache

    yield TestClient(app)


@pytest_asyncio.fixture()
async def get_token_confirmed():
    token = await create_access_token(data={"sub": test_user_confirmed_obj["username"]})
    return token


@pytest_asyncio.fixture()
async def get_token_admin():
    token = await create_access_token(data={"sub": test_user_admin_obj["username"]})
    return token


@pytest_asyncio.fixture()
async def get_token_not_confirmed():
    token = await create_access_token(
        data={"sub": test_user_not_confirmed_obj["username"]}
    )
    return token


@pytest.fixture(scope="module")
def mock_redis():
    """
    Fixture to mock Redis client.
    """
    with patch("src.cache.cache.from_url") as mock_from_url:
        redis_instance = AsyncMock()
        redis_instance.get.return_value = None
        redis_instance.set.return_value = True
        mock_from_url.return_value = redis_instance
        yield redis_instance


@pytest.fixture
def mock_cloudinary():
    """
    Fixture to mock Cloudinary.
    """
    with patch("cloudinary.uploader.upload") as mock_upload, patch(
        "cloudinary.CloudinaryImage"
    ) as mock_image:
        mock_upload.return_value = {"url": "http://mocked-url.com"}
        mock_image.return_value.build_url.return_value = "http://mocked-url.com"
        yield mock_upload, mock_image


@pytest_asyncio.fixture()
async def get_admin_token():
    """
    Fixture to generate a token for an admin user.
    """
    admin_user = {
        "username": "adminuser",
        "email": "admin@example.com",
        "role": "admin",
    }
    token = await create_access_token(
        data={"sub": admin_user["username"], "role": admin_user["role"]}
    )
    return token
