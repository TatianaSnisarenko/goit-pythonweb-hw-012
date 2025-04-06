from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import or_, and_, extract
from datetime import date

from src.database.models import Contact
from src.schemas import ContactModel, User

"""
Repository module for managing contacts.

This module provides a `ContactRepository` class that contains methods for 
performing CRUD operations on contacts, as well as additional functionality 
such as searching contacts and retrieving upcoming birthdays.

Classes:
    ContactRepository: A repository class for managing contact-related operations.
"""


class ContactRepository:
    """
    A repository class for managing contact-related operations.

    This class provides methods for performing CRUD operations on contacts,
    searching contacts, and retrieving upcoming birthdays.

    Attributes:
        db (AsyncSession): The database session used for executing queries.
    """

    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(self, skip: int, limit: int, user: User) -> List[Contact]:
        """
        Retrieve a paginated list of contacts for a specific user.

        Args:
            skip (int): The number of records to skip.
            limit (int): The maximum number of records to retrieve.
            user (User): The user whose contacts are being retrieved.

        Returns:
            List[Contact]: A list of contacts belonging to the user.
        """
        stmt = select(Contact).filter_by(user=user).offset(skip).limit(limit)
        contacts = await self.db.execute(stmt)
        return contacts.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact | None:
        """
        Retrieve a specific contact by its ID for a specific user.

        Args:
            contact_id (int): The ID of the contact to retrieve.
            user (User): The user who owns the contact.

        Returns:
            Contact | None: The contact if found, otherwise None.
        """
        stmt = select(Contact).filter_by(id=contact_id, user=user)
        contact = await self.db.execute(stmt)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactModel, user: User) -> Contact:
        """
        Create a new contact for a specific user.

        Args:
            body (ContactModel): The data for the new contact.
            user (User): The user who owns the contact.

        Returns:
            Contact: The newly created contact.
        """
        contact = Contact(**body.model_dump(exclude_unset=True), user=user)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return await self.get_contact_by_id(contact.id, user)

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        """
        Remove a specific contact by its ID for a specific user.

        Args:
            contact_id (int): The ID of the contact to remove.
            user (User): The user who owns the contact.

        Returns:
            Contact | None: The removed contact if found, otherwise None.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactModel, user: User
    ) -> Contact | None:
        """
        Update a specific contact by its ID for a specific user.

        Args:
            contact_id (int): The ID of the contact to update.
            body (ContactModel): The updated data for the contact.
            user (User): The user who owns the contact.

        Returns:
            Contact | None: The updated contact if found, otherwise None.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for key, value in body.dict(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)

        return contact

    async def search_contacts(
        self,
        skip: int,
        limit: int,
        first_name: Optional[str],
        last_name: Optional[str],
        email: Optional[str],
        user: User,
    ) -> List[Contact]:
        """
        Search for contacts by first name, last name, or email for a specific user.

        Args:
            skip (int): The number of records to skip.
            limit (int): The maximum number of records to retrieve.
            first_name (Optional[str]): The first name to search for.
            last_name (Optional[str]): The last name to search for.
            email (Optional[str]): The email to search for.
            user (User): The user whose contacts are being searched.

        Returns:
            List[Contact]: A list of contacts matching the search criteria.
        """
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
        """
        Retrieve contacts with upcoming birthdays within a specified date range.

        Args:
            today (date): The start date of the range.
            next_date (date): The end date of the range.
            skip (int): The number of records to skip.
            limit (int): The maximum number of records to retrieve.
            user (User): The user whose contacts are being retrieved.

        Returns:
            List[Contact]: A list of contacts with upcoming birthdays.
        """

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
