from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.schemas import ContactModel, ContactResponse, User
from src.services.auth import get_current_user
from src.services.contacts import ContactService


router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=List[ContactResponse])
async def read_contacts(
    skip: int = Query(0, ge=0, description="Number of records to skip (must be >= 0)"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return (1-100)"
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get a list of contacts with pagination.
    - `skip`: Number of records to skip (default: 0, must be >= 0).
    - `limit`: Maximum number of records to return (default: 10, range: 1-100).
    """
    contact_service = ContactService(db)
    contacts = await contact_service.get_contacts(skip, limit, user)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get a single contact by its ID.
    - `contact_id`: The ID of the contact to retrieve.
    """
    contact_service = ContactService(db)
    contact = await contact_service.get_contact(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactModel,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Create a new contact.
    - `body`: The contact data to create.
    """
    contact_service = ContactService(db)
    return await contact_service.create_contact(body, user)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    body: ContactModel,
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Update an existing contact by its ID.
    - `contact_id`: The ID of the contact to update.
    - `body`: The updated contact data.
    """
    contact_service = ContactService(db)
    contact = await contact_service.update_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.delete("/{contact_id}", response_model=ContactResponse)
async def remove_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Delete a contact by its ID.
    - `contact_id`: The ID of the contact to delete.
    """
    contact_service = ContactService(db)
    contact = await contact_service.remove_contact(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.get("/search/", response_model=List[ContactResponse])
async def search_contacts(
    skip: int = Query(0, ge=0, description="Number of records to skip (must be >= 0)"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return (1-100)"
    ),
    first_name: Optional[str] = Query(
        None, description="Filter contacts by first name (case-insensitive)"
    ),
    last_name: Optional[str] = Query(
        None, description="Filter contacts by last name (case-insensitive)"
    ),
    email: Optional[str] = Query(
        None, description="Filter contacts by email address (case-insensitive)"
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Search contacts by first name, last name, or email with pagination.
    - `skip`: Number of records to skip (default: 0, must be >= 0).
    - `limit`: Maximum number of records to return (default: 10, range: 1-100).
    - `first_name`: Filter by first name (optional).
    - `last_name`: Filter by last name (optional).
    - `email`: Filter by email address (optional).
    """
    contact_service = ContactService(db)
    contacts = await contact_service.search_contacts(
        skip, limit, first_name, last_name, email, user
    )
    return contacts


@router.get("/birthdays/", response_model=List[ContactResponse])
async def get_upcoming_birthdays(
    days: int = Query(
        7,
        ge=1,
        le=364,
        description="Number of days to look ahead for birthdays (default: 7, range: 1-364)",
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip (must be >= 0)"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return (1-100)"
    ),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Get a list of contacts with birthdays in the next `days` days, with pagination.
    - `days`: Number of days to look ahead for birthdays (default: 7, range: 1-364).
    - `skip`: Number of records to skip (default: 0, must be >= 0).
    - `limit`: Maximum number of records to return (default: 10, range: 1-100).
    """
    contact_service = ContactService(db)
    contacts = await contact_service.get_upcoming_birthdays(days, skip, limit, user)
    return contacts
