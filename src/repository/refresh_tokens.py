from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import RefreshToken

"""
Repository module for managing refresh tokens.

This module provides a `RefreshTokenRepository` class that contains methods 
for performing CRUD operations on refresh tokens.

Classes:
    RefreshTokenRepository: A repository class for managing refresh token-related operations.
"""


class RefreshTokenRepository:
    """
    A repository class for managing refresh token-related operations.

    This class provides methods for creating, updating, and retrieving refresh tokens.

    Attributes:
        db (AsyncSession): The database session used for executing queries.
    """

    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        """
        Create a new refresh token.

        Args:
            refresh_token (RefreshToken): The refresh token to be created.

        Returns:
            RefreshToken: The newly created refresh token.
        """
        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)
        return refresh_token

    async def update_refresh_token(
        self, old_refresh_token: str, refresh_token: RefreshToken, user_id: int
    ) -> RefreshToken:
        """
        Update an existing refresh token with new values.

        Args:
            old_refresh_token (str): The old refresh token string to be updated.
            refresh_token (RefreshToken): The new refresh token data.
            user_id (int): The ID of the user associated with the refresh token.

        Returns:
            RefreshToken: The updated refresh token if found, otherwise None.
        """

        stmt = select(RefreshToken).filter_by(token=old_refresh_token, user_id=user_id)
        existing_token = (await self.db.execute(stmt)).scalar_one_or_none()

        if existing_token:
            existing_token.token = refresh_token.token
            existing_token.expires_at = refresh_token.expires_at
            existing_token.created_at = refresh_token.created_at
            await self.db.commit()
            await self.db.refresh(existing_token)
        return existing_token
