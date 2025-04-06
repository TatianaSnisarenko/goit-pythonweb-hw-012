import contextlib
from src.conf.config import settings

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

"""
Database session management module.

This module provides a `DatabaseSessionManager` class for managing database 
sessions using SQLAlchemy's asynchronous engine. It also includes a dependency 
function `get_db` for integrating database sessions with FastAPI.

Classes:
    DatabaseSessionManager: Manages the creation and lifecycle of database sessions.

Functions:
    get_db: Dependency function for providing a database session to FastAPI routes.
"""


class DatabaseSessionManager:
    """
    Manages the creation and lifecycle of asynchronous database sessions.

    This class uses SQLAlchemy's asynchronous engine to create and manage
    database sessions. It provides an async context manager for handling
    sessions, ensuring proper cleanup and rollback in case of errors.

    Attributes:
        _engine (AsyncEngine): The SQLAlchemy asynchronous engine instance.
        _session_maker (async_sessionmaker): The session maker for creating database sessions.

    Methods:
        session: Async context manager for creating and managing a database session.
    """

    def __init__(self, url: str):
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Async context manager for creating and managing a database session.

        This method yields a database session and ensures proper cleanup
        (e.g., rollback on errors and session closure).

        Yields:
            AsyncSession: An instance of the SQLAlchemy asynchronous session.

        Raises:
            Exception: If the session maker is not initialized.
            SQLAlchemyError: If an error occurs during the session lifecycle.
        """
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """
    Dependency function for providing a database session to FastAPI routes.

    This function uses the `DatabaseSessionManager` to create a new database
    session and yields it for use in FastAPI routes. The session is automatically
    closed after the route handler completes.

    Yields:
        AsyncSession: An instance of the SQLAlchemy asynchronous session.
    """
    async with sessionmanager.session() as session:
        yield session
