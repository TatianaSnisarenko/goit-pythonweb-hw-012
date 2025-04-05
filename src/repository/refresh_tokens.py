from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def create_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)
        return refresh_token

    async def update_refresh_token(
        self, old_refresh_token: str, refresh_token: RefreshToken, user_id: int
    ) -> RefreshToken:

        stmt = select(RefreshToken).filter_by(token=old_refresh_token, user_id=user_id)
        existing_token = (await self.db.execute(stmt)).scalar_one_or_none()

        if existing_token:
            existing_token.token = refresh_token.token
            existing_token.expires_at = refresh_token.expires_at
            existing_token.created_at = refresh_token.created_at
            await self.db.commit()
            await self.db.refresh(existing_token)
        return existing_token
