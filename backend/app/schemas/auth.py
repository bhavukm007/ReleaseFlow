from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("password")
    @classmethod
    def bcrypt_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def bcrypt_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return value


class UserRead(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    created_at: datetime
    last_login: datetime | None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserRead
