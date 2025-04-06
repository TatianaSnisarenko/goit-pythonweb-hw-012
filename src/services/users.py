from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.repository.users import UserRepository
from src.schemas import User, UserCreate

"""
Service module for managing user-related operations.

This module provides the `UserService` class, which contains methods for 
performing CRUD operations on users, confirming emails, resetting passwords, 
and updating user avatars.

Classes:
    UserService: A service class for managing user-related operations.
"""


class UserService:
    """
    A service class for managing user-related operations.

    This class provides methods for performing CRUD operations on users,
    confirming emails, resetting passwords, and updating user avatars.

    Attributes:
        repository (UserRepository): The repository for executing user-related database operations.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the UserService with a database session.

        Args:
            db (AsyncSession): The database session used for executing queries.
        """
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate) -> User:
        """
        Creates a new user and generates a Gravatar avatar if available.

        Args:
            body (UserCreate): The data for the new user.

        Returns:
            User: The newly created user.
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieves a user by their ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User | None: The user if found, otherwise None.
        """
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieves a user by their username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            User | None: The user if found, otherwise None.
        """
        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieves a user by their email address.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            User | None: The user if found, otherwise None.
        """
        return await self.repository.get_user_by_email(email)

    async def confirmed_email(self, email: str) -> None:
        """
        Confirms a user's email address.

        Args:
            email (str): The email address of the user to confirm.

        Returns:
            None
        """
        return await self.repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Updates a user's avatar URL.

        Args:
            email (str): The email address of the user.
            url (str): The new avatar URL.

        Returns:
            User: The updated user.
        """
        return await self.repository.update_avatar_url(email, url)

    async def get_user_by_username_and_by_refresh_token(
        self, username: str, token: str
    ) -> User | None:
        """
        Retrieves a user by their username and refresh token.

        Args:
            username (str): The username of the user to retrieve.
            token (str): The refresh token associated with the user.

        Returns:
            User | None: The user if found, otherwise None.
        """
        return await self.repository.get_user_by_username_and_by_refresh_token(
            username, token
        )

    async def reset_password(self, email: str, hashed_password: str) -> None:
        """
        Resets a user's password.

        Args:
            email (str): The email address of the user.
            hashed_password (str): The new hashed password.

        Returns:
            None
        """
        return await self.repository.reset_password(email, hashed_password)
