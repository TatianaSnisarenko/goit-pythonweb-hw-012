from pydantic import ConfigDict, EmailStr
from pydantic_settings import BaseSettings

"""
Configuration module for the application.

This module defines the `Settings` class, which uses Pydantic's `BaseSettings` 
to load and validate environment variables. These settings are used throughout 
the application for database connections, JWT authentication, email services, 
Cloudinary integration, and Redis caching.

Classes:
    Settings: A Pydantic-based settings class for managing application configuration.

Attributes:
    settings (Settings): An instance of the `Settings` class, preloaded with 
        environment variables.
"""


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        DB_URL (str): The database connection URL.
        JWT_SECRET (str): The secret key for JWT token generation.
        JWT_ALGORITHM (str): The algorithm used for JWT tokens (default: "HS256").
        ACCESS_TOKEN_EXPIRATION_SECONDS (int): Expiration time for access tokens in seconds (default: 3600).
        REFRESH_TOKEN_EXPIRATION_SECONDS (int): Expiration time for refresh tokens in seconds (default: 604800).
        MAIL_USERNAME (EmailStr): The email username for the SMTP server.
        MAIL_PASSWORD (str): The email password for the SMTP server.
        MAIL_FROM (EmailStr): The email address used as the sender.
        MAIL_PORT (int): The port for the SMTP server.
        MAIL_SERVER (str): The SMTP server address.
        MAIL_FROM_NAME (str): The name displayed as the sender (default: "Contacts API Service").
        MAIL_STARTTLS (bool): Whether to use STARTTLS for the SMTP connection (default: False).
        MAIL_SSL_TLS (bool): Whether to use SSL/TLS for the SMTP connection (default: True).
        USE_CREDENTIALS (bool): Whether to use credentials for the SMTP connection (default: True).
        VALIDATE_CERTS (bool): Whether to validate SSL certificates (default: True).
        CLOUDINARY_NAME (str): The Cloudinary account name.
        CLOUDINARY_API_KEY (int): The Cloudinary API key.
        CLOUDINARY_API_SECRET (str): The Cloudinary API secret.
        REDIS_URL (str): The Redis connection URL.
    """

    DB_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRATION_SECONDS: int = 3600  # 1 hour
    REFRESH_TOKEN_EXPIRATION_SECONDS: int = 604800  # 7 days
    model_config = ConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8"
    )
    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str = "Contacts API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: int
    CLOUDINARY_API_SECRET: str
    REDIS_URL: str


settings = Settings()
