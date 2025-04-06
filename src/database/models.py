from datetime import datetime, date
from sqlalchemy import (
    TIMESTAMP,
    Column,
    Integer,
    String,
    Boolean,
    func,
    Enum as SqlEnum,
)
from sqlalchemy.orm import relationship, mapped_column, Mapped, DeclarativeBase
from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import DateTime, Date
from enum import Enum

"""
Database models module.

This module defines the SQLAlchemy ORM models for the application, including 
users, contacts, and refresh tokens. It uses SQLAlchemy's `DeclarativeBase` 
for model definitions and includes relationships between models.

Classes:
    Base: The declarative base class for all models.
    UserRole: An enumeration for user roles (e.g., USER, ADMIN).
    Contact: Represents a contact entity associated with a user.
    User: Represents a user entity with authentication and role information.
    RefreshToken: Represents a refresh token for user authentication.
"""


class Base(DeclarativeBase):
    """
    The declarative base class for all database models.

    This class is used as the base for all SQLAlchemy ORM models in the application.
    """

    pass


class UserRole(str, Enum):
    """
    Enumeration for user roles.

    Attributes:
        USER (str): Represents a regular user role.
        ADMIN (str): Represents an administrator role.
    """

    USER = "user"
    ADMIN = "admin"


class Contact(Base):
    """
    Represents a contact entity associated with a user.

    Attributes:
        id (int): The primary key of the contact.
        first_name (str): The first name of the contact.
        last_name (str): The last name of the contact.
        email (str): The email address of the contact.
        phone (str): The phone number of the contact.
        birthday (date): The birthday of the contact.
        created_at (datetime): The timestamp when the contact was created.
        updated_at (datetime): The timestamp when the contact was last updated.
        user_id (int): The ID of the user who owns the contact.
        user (User): The user associated with the contact.
    """

    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("email", "user_id", name="unique_email_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(15), nullable=False)
    birthday: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, default=func.now(), onupdate=func.now()
    )
    user_id = Column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), default=None
    )
    user = relationship("User", backref="contacts")


class User(Base):
    """
    Represents a user entity with authentication and role information.

    Attributes:
        id (int): The primary key of the user.
        username (str): The username of the user.
        email (str): The email address of the user.
        hashed_password (str): The hashed password of the user.
        created_at (datetime): The timestamp when the user was created.
        avatar (str | None): The URL of the user's avatar (optional).
        confirmed (bool): Indicates whether the user's email is confirmed.
        role (UserRole): The role of the user (e.g., USER, ADMIN).
        refresh_tokens (list[RefreshToken]): The list of refresh tokens associated with the user.
    """

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole),
        default=UserRole.USER,
        server_default=UserRole.USER,
        nullable=False,
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    """
    Represents a refresh token for user authentication.

    Attributes:
        id (int): The primary key of the refresh token.
        token (str): The refresh token string.
        created_at (datetime): The timestamp when the token was created.
        expires_at (datetime): The timestamp when the token expires.
        user_id (int): The ID of the user associated with the token.
        user (User): The user associated with the refresh token.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
