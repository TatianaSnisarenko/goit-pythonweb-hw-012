from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.refresh_tokens import RefreshTokenRepository
from src.database.models import RefreshToken
from src.schemas import TokenDto


class RefreshTokenService:

    def __init__(self, db: AsyncSession):
        self.repository = RefreshTokenRepository(db)

    async def create_refresh_token(
        self, refresh_token: TokenDto, user_id: int
    ) -> RefreshToken:
        refresh_token_obj = self.map_refresh_token(refresh_token, user_id)
        return await self.repository.create_refresh_token(refresh_token_obj)

    async def update_refresh_token(
        self, old_refresh_token: str, refresh_token: TokenDto, user_id: int
    ) -> RefreshToken:
        refresh_token_obj = self.map_refresh_token(refresh_token, user_id)
        return await self.repository.update_refresh_token(
            old_refresh_token, refresh_token_obj, user_id
        )

    def map_refresh_token(self, refresh_token, user_id):
        return RefreshToken(
            token=refresh_token.token,
            expires_at=refresh_token.expires_at,
            created_at=refresh_token.created_at,
            user_id=user_id,
        )
