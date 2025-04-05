from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.repository.contacts import ContactRepository
from src.schemas import ContactModel, User


def _handle_integrity_error(e: IntegrityError):
    if "unique_email_user" in str(e.orig):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with such email already exists",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error",
        )


class ContactService:
    def __init__(self, db: AsyncSession):
        self.contact_repository = ContactRepository(db)

    async def create_contact(self, body: ContactModel, user: User):
        try:
            return await self.contact_repository.create_contact(body, user)
        except IntegrityError as e:
            await self.contact_repository.db.rollback()
            _handle_integrity_error(e)

    async def get_contacts(self, skip: int, limit: int, user: User):
        return await self.contact_repository.get_contacts(skip, limit, user)

    async def get_contact(self, contact_id: int, user: User):
        return await self.contact_repository.get_contact_by_id(contact_id, user)

    async def update_contact(self, contact_id: int, body: ContactModel, user: User):
        try:
            return await self.contact_repository.update_contact(contact_id, body, user)
        except IntegrityError as e:
            await self.contact_repository.db.rollback()
            _handle_integrity_error(e)

    async def remove_contact(self, contact_id: int, user: User):
        return await self.contact_repository.remove_contact(contact_id, user)

    async def search_contacts(
        self,
        skip,
        limit,
        first_name: Optional[str],
        last_name: Optional[str],
        email: Optional[str],
        user: User,
    ) -> List[ContactModel]:
        return await self.contact_repository.search_contacts(
            skip, limit, first_name, last_name, email, user
        )

    async def get_upcoming_birthdays(
        self, days: int, skip: int, limit: int, user: User
    ) -> List[ContactModel]:
        today = date.today()
        next_date = today + timedelta(days=days)
        return await self.contact_repository.get_upcoming_birthdays(
            today, next_date, skip, limit, user
        )
