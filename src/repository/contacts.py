from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import or_, and_, extract
from datetime import date

from src.database.models import Contact
from src.schemas import ContactModel, User


class ContactRepository:
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(self, skip: int, limit: int, user: User) -> List[Contact]:
        stmt = select(Contact).filter_by(user=user).offset(skip).limit(limit)
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact:
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return await self.get_contact_by_id(contact.id, user)

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactModel, user: User
    ) -> Contact | None:
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for key, value in body.dict(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    async def search_contacts(
        self,
        skip,
        limit,
        first_name: Optional[str],
        last_name: Optional[str],
        email: Optional[str],
        user: User,
    ) -> List[Contact]:
        stmt = select(Contact)
        if first_name:
            stmt = stmt.filter(Contact.first_name.ilike(f"%{first_name}%"))
        if last_name:
            stmt = stmt.filter(Contact.last_name.ilike(f"%{last_name}%"))
        if email:
            stmt = stmt.filter(Contact.email.ilike(f"%{email}%"))
        stmt = stmt.filter_by(user=user).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_upcoming_birthdays(
        self, today: date, next_date: date, skip: int, limit: int, user: User
    ) -> List[Contact]:

        start_day_of_year = today.timetuple().tm_yday
        end_day_of_year = next_date.timetuple().tm_yday

        if start_day_of_year <= end_day_of_year:
            stmt = (
                select(Contact)
                .filter_by(user=user)
                .filter(
                    or_(
                        and_(
                            extract("doy", Contact.birthday) >= start_day_of_year,
                            extract("doy", Contact.birthday) <= end_day_of_year,
                        )
                    )
                )
                .order_by(extract("doy", Contact.birthday))
                .offset(skip)
                .limit(limit)
            )
        else:
            stmt = (
                select(Contact)
                .filter_by(user=user)
                .filter(
                    or_(
                        extract("doy", Contact.birthday) >= start_day_of_year,
                        extract("doy", Contact.birthday) <= end_day_of_year,
                    )
                )
                .order_by(extract("doy", Contact.birthday))
                .offset(skip)
                .limit(limit)
            )

        result = await self.db.execute(stmt)
        return result.scalars().all()
