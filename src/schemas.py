from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator

from src.database.models import UserRole

"""
Schemas module.

This module defines Pydantic models (schemas) used for data validation and 
serialization in the application. These schemas are used for handling 
contacts, users, authentication tokens, and other data structures.

Classes:
    ContactModel: Schema for creating or updating a contact.
    ContactResponse: Schema for returning contact data in API responses.
    User: Schema for returning user data in API responses.
    UserCreate: Schema for creating a new user with validation.
    Token: Schema for authentication tokens.
    TokenRefreshRequest: Schema for requesting a token refresh.
    TokenDto: Schema for internal token representation.
    RequestEmail: Schema for email-based requests.
    HealthCheckResponse: Schema for health check responses.
"""


class ContactModel(BaseModel):
    """
    Schema for creating or updating a contact.

    Attributes:
        first_name (str): The first name of the contact (max length: 50).
        last_name (str): The last name of the contact (max length: 50).
        email (EmailStr | None): The email address of the contact (optional).
        phone (str): The phone number of the contact (10-15 digits, optional "+" prefix).
        birthday (date | None): The birthday of the contact (optional).
    """

    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: EmailStr | None
    phone: str = Field(max_length=15, pattern=r"^\+?\d{10,15}$")
    birthday: date | None


class ContactResponse(ContactModel):
    """
    Schema for returning contact data in API responses.

    Attributes:
        id (int): The unique identifier of the contact.
        created_at (Optional[datetime]): The timestamp when the contact was created.
        updated_at (Optional[datetime]): The timestamp when the contact was last updated.
    """

    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    """
    Schema for returning user data in API responses.

    Attributes:
        id (int): The unique identifier of the user.
        username (str): The username of the user.
        email (str): The email address of the user.
        role (UserRole): The role of the user (e.g., USER, ADMIN).
        avatar (str): The URL of the user's avatar.
    """

    id: int
    username: str
    email: str
    role: UserRole
    avatar: str
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """
    Schema for creating a new user with validation.

    Attributes:
        username (str): The username of the user (min length: 3, max length: 50).
        email (EmailStr): The email address of the user.
        password (str): The password of the user (min length: 8, max length: 50).
        role (UserRole): The role of the user (e.g., USER, ADMIN).
    """

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=50)
    role: UserRole

    @field_validator("password")
    def validate_password(cls, value: str) -> str:
        """
        Validates the password to ensure it meets complexity requirements.

        Args:
            value (str): The password to validate.

        Returns:
            str: The validated password.

        Raises:
            ValueError: If the password does not meet complexity requirements.
        """
        if not any(char.islower() for char in value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit.")
        if not any(char in "@$!%*?&" for char in value):
            raise ValueError(
                "Password must contain at least one special character (@$!%*?&)."
            )
        return value


class Token(BaseModel):
    """
    Schema for authentication tokens.

    Attributes:
        access_token (str): The access token.
        refresh_token (str): The refresh token.
        token_type (str): The type of the token (e.g., "bearer").
    """

    access_token: str
    refresh_token: str
    token_type: str


class TokenRefreshRequest(BaseModel):
    """
    Schema for requesting a token refresh.

    Attributes:
        refresh_token (str): The refresh token to use for refreshing the access token.
    """

    refresh_token: str


class TokenDto(BaseModel):
    """
    Schema for internal token representation.

    Attributes:
        token (str): The token string.
        expires_at (datetime): The expiration timestamp of the token.
        created_at (datetime): The creation timestamp of the token.
    """

    token: str
    expires_at: datetime
    created_at: datetime


class RequestEmail(BaseModel):
    """
    Schema for email-based requests.

    Attributes:
        email (EmailStr): The email address for the request.
    """

    email: EmailStr


class HealthCheckResponse(BaseModel):
    """
    Schema for health check responses.

    Attributes:
        message (str): The health check message.
    """

    message: str
