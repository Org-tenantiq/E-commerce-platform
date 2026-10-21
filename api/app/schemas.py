"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, EmailStr, field_validator

from api.app.passwords import MAX_PASSWORD_BYTES, MIN_PASSWORD_LENGTH


def _strip(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


NormalizedEmail = Annotated[EmailStr, BeforeValidator(_strip), AfterValidator(str.lower)]


class RegisterRequest(BaseModel):
    """Payload for registering a new customer account."""

    email: NormalizedEmail
    password: str

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str) -> str:
        """Enforce the minimum length and the bcrypt byte limit."""
        if len(value) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(f"password must be at most {MAX_PASSWORD_BYTES} bytes")
        return value


class UserRead(BaseModel):
    """Public representation of a user; never includes credentials."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    created_at: datetime


class LoginRequest(BaseModel):
    """Payload for logging in."""

    email: NormalizedEmail
    password: str


class TokenResponse(BaseModel):
    """Access token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    """The authenticated caller."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
