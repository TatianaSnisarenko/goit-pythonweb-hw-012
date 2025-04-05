from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


class ContactModel(BaseModel):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: EmailStr | None
    phone: str = Field(max_length=15, pattern=r"^\+?\d{10,15}$")
    birthday: date | None


class ContactResponse(ContactModel):
    id: int
    created_at: Optional[datetime] | None
    updated_at: Optional[datetime] | None
    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    id: int
    username: str
    email: str
    avatar: str
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=50)

    @field_validator("password")
    def validate_password(cls, value: str) -> str:
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
    access_token: str
    token_type: str


class RequestEmail(BaseModel):
    email: EmailStr


class HealthCheckResponse(BaseModel):
    message: str
