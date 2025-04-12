from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import UserCreate
from sqlalchemy.orm import joinedload

"""
Repository module for managing user-related operations.

This module provides a `UserRepository` class that contains methods for 
performing CRUD operations on users, as well as additional functionality 
such as email confirmation, password reset, and avatar updates.

Classes:
    UserRepository: A repository class for managing user-related operations.
"""


class UserRepository:
    """
    A repository class for managing user-related operations.

    This class provides methods for performing CRUD operations on users,
    confirming emails, resetting passwords, and updating user avatars.

    Attributes:
        db (AsyncSession): The database session used for executing queries.
    """

    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a user by their ID.

        Args:
            user_id (int): The ID of the user to retrieve.

        Returns:
            User | None: The user if found, otherwise None.
        """
        stmt = select(User).filter_by(id=user_id)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieve a user by their username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            User | None: The user if found, otherwise None.
        """
        stmt = select(User).filter_by(username=username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by their email address.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            User | None: The user if found, otherwise None.
        """
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_username_and_by_refresh_token(
        self, username: str, token: str
    ) -> User | None:
        """
        Retrieve a user by their username and refresh token.

        Args:
            username (str): The username of the user to retrieve.
            token (str): The refresh token associated with the user.

        Returns:
            User | None: The user if found, otherwise None.
        """
        stmt = (
            select(User)
            .options(joinedload(User.refresh_tokens))
            .filter(User.username == username)
            .filter(User.refresh_tokens.any(token=token))
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: str = None) -> User:
        """
        Create a new user.

        Args:
            body (UserCreate): The data for the new user.
            avatar (str, optional): The URL of the user's avatar. Defaults to None.

        Returns:
            User: The newly created user.
        """
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=body.password,
            avatar=avatar
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Confirm a user's email address.

        Args:
            email (str): The email address of the user to confirm.

        Returns:
            None
        """
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def reset_password(self, email: str, hashed_password: str) -> None:
        """
        Reset a user's password.

        Args:
            email (str): The email address of the user.
            hashed_password (str): The new hashed password.

        Returns:
            None
        """
        user = await self.get_user_by_email(email)
        user.hashed_password = hashed_password
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Update a user's avatar URL.

        Args:
            email (str): The email address of the user.
            url (str): The new avatar URL.

        Returns:
            User: The updated user.
        """
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user_role(self, user_id: int, new_role: str) -> User:
        """
        Update the role of a user.

        Args:
            user_id (int): The ID of the user whose role is to be updated.
            new_role (str): The new role to assign to the user.

        Returns:
            User: The updated user object.
        """
        user = await self.get_user_by_id(user_id)
        user.role = new_role
        await self.db.commit()
        await self.db.refresh(user)
        return user
