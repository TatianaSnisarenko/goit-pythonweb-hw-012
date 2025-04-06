from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.refresh_tokens import RefreshTokenRepository
from src.database.models import RefreshToken
from src.schemas import TokenDto

"""
Service module for managing refresh tokens.

This module provides a `RefreshTokenService` class that contains methods for 
creating, updating, and mapping refresh tokens. It interacts with the 
`RefreshTokenRepository` to perform database operations.

Classes:
    RefreshTokenService: A service class for managing refresh token-related operations.
"""


class RefreshTokenService:
    """
    A service class for managing refresh token-related operations.

    This class provides methods for creating, updating, and mapping refresh tokens.
    It interacts with the `RefreshTokenRepository` to perform database operations.

    Attributes:
        repository (RefreshTokenRepository): The repository for executing refresh token-related database operations.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the RefreshTokenService with a database session.

        Args:
            db (AsyncSession): The database session used for executing queries.
        """
        self.repository = RefreshTokenRepository(db)

    async def create_refresh_token(
        self, refresh_token: TokenDto, user_id: int
    ) -> RefreshToken:
        """
        Creates a new refresh token for a user.

        Args:
            refresh_token (TokenDto): The data for the new refresh token.
            user_id (int): The ID of the user associated with the refresh token.

        Returns:
            RefreshToken: The newly created refresh token.
        """
        refresh_token_obj = self.map_refresh_token(refresh_token, user_id)
        return await self.repository.create_refresh_token(refresh_token_obj)

    async def update_refresh_token(
        self, old_refresh_token: str, refresh_token: TokenDto, user_id: int
    ) -> RefreshToken:
        """
        Updates an existing refresh token with a new one.

        Args:
            old_refresh_token (str): The old refresh token string to be replaced.
            refresh_token (TokenDto): The new refresh token data.
            user_id (int): The ID of the user associated with the refresh token.

        Returns:
            RefreshToken: The updated refresh token.
        """
        refresh_token_obj = self.map_refresh_token(refresh_token, user_id)
        return await self.repository.update_refresh_token(
            old_refresh_token, refresh_token_obj, user_id
        )

    def map_refresh_token(self, refresh_token: TokenDto, user_id: int) -> RefreshToken:
        """
        Maps a TokenDto object to a RefreshToken model.

        Args:
            refresh_token (TokenDto): The data transfer object for the refresh token.
            user_id (int): The ID of the user associated with the refresh token.

        Returns:
            RefreshToken: The mapped refresh token model.
        """
        return RefreshToken(
            token=refresh_token.token,
            expires_at=refresh_token.expires_at,
            created_at=refresh_token.created_at,
            user_id=user_id,
        )
