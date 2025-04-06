from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.repository.contacts import ContactRepository
from src.schemas import ContactModel, User
from src.utils.utils import to_dict

"""
Service module for managing contacts.

This module provides a `ContactService` class that contains methods for 
performing CRUD operations on contacts, searching contacts, and retrieving 
upcoming birthdays. It also includes utility functions for handling database 
integrity errors.

Classes:
    ContactService: A service class for managing contact-related operations.

Functions:
    _handle_integrity_error: Handles database integrity errors and raises appropriate HTTP exceptions.
"""


def _handle_integrity_error(e: IntegrityError) -> None:
    """
    Handles database integrity errors and raises appropriate HTTP exceptions.

    Args:
        e (IntegrityError): The SQLAlchemy integrity error to handle.

    Raises:
        HTTPException: If the error is related to a unique constraint or other database integrity issues.
    """
    if "unique_email_user" in str(e.orig):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with such email already exists",
        )
    else:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error",
        )


class ContactService:
    """
    A service class for managing contact-related operations.

    This class provides methods for performing CRUD operations on contacts,
    searching contacts, and retrieving upcoming birthdays.

    Attributes:
        contact_repository (ContactRepository): The repository for executing contact-related database operations.
    """

    def __init__(self, db: AsyncSession):
        self.contact_repository = ContactRepository(db)

    async def create_contact(self, body: ContactModel, user: User) -> ContactModel:
        """
        Create a new contact for a specific user.

        Args:
            body (ContactModel): The data for the new contact.
            user (User): The user who owns the contact.

        Returns:
            ContactModel: The newly created contact.

        Raises:
            HTTPException: If a contact with the same email already exists.
        """
        try:
            return await self.contact_repository.create_contact(body, user)
        except IntegrityError as e:
            await self.contact_repository.db.rollback()
            _handle_integrity_error(e)

    async def get_contacts(
        self, skip: int, limit: int, user: User
    ) -> List[ContactModel]:
        """
        Retrieve a paginated list of contacts for a specific user.

        Args:
            skip (int): The number of records to skip.
            limit (int): The maximum number of records to retrieve.
            user (User): The user whose contacts are being retrieved.

        Returns:
            List[ContactModel]: A list of contacts belonging to the user.
        """
        return await self.contact_repository.get_contacts(skip, limit, user)

    async def get_contact(self, contact_id: int, user: User) -> Optional[ContactModel]:
        """
        Retrieve a specific contact by its ID for a specific user.

        Args:
            contact_id (int): The ID of the contact to retrieve.
            user (User): The user who owns the contact.

        Returns:
            Optional[ContactModel]: The contact if found, otherwise None.
        """
        return await self.contact_repository.get_contact_by_id(contact_id, user)

    async def update_contact(
        self, contact_id: int, body: ContactModel, user: User
    ) -> Optional[ContactModel]:
        """
        Update a specific contact by its ID for a specific user.

        Args:
            contact_id (int): The ID of the contact to update.
            body (ContactModel): The updated data for the contact.
            user (User): The user who owns the contact.

        Returns:
            Optional[ContactModel]: The updated contact if found, otherwise None.

        Raises:
            HTTPException: If a contact with the same email already exists.
        """
        try:
            return await self.contact_repository.update_contact(contact_id, body, user)
        except IntegrityError as e:
            await self.contact_repository.db.rollback()
            _handle_integrity_error(e)

    async def remove_contact(
        self, contact_id: int, user: User
    ) -> Optional[ContactModel]:
        """
        Remove a specific contact by its ID for a specific user.

        Args:
            contact_id (int): The ID of the contact to remove.
            user (User): The user who owns the contact.

        Returns:
            Optional[ContactModel]: The removed contact if found, otherwise None.
        """
        return await self.contact_repository.remove_contact(contact_id, user)

    async def search_contacts(
        self,
        skip: int,
        limit: int,
        first_name: Optional[str],
        last_name: Optional[str],
        email: Optional[str],
        user: User,
    ) -> List[ContactModel]:
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
            List[ContactModel]: A list of contacts matching the search criteria.
        """
        return await self.contact_repository.search_contacts(
            skip, limit, first_name, last_name, email, user
        )

    async def get_upcoming_birthdays(
        self, days: int, skip: int, limit: int, user: User
    ) -> List[ContactModel]:
        """
        Retrieve contacts with upcoming birthdays within a specified date range.

        Args:
            days (int): The number of days ahead to search for birthdays.
            skip (int): The number of records to skip.
            limit (int): The maximum number of records to retrieve.
            user (User): The user whose contacts are being retrieved.

        Returns:
            List[ContactModel]: A list of contacts with upcoming birthdays.
        """
        today = date.today()
        next_date = today + timedelta(days=days)
        return await self.contact_repository.get_upcoming_birthdays(
            today, next_date, skip, limit, user
        )
