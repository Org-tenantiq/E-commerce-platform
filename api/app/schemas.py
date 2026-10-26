from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from datetime import datetime
from typing import Optional


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator('email')
    @classmethod
    def email_must_be_stripped(cls, v):
        if v != v.strip():
            raise ValueError('email must not have leading or trailing spaces')
        return v

    @field_validator('password')
    @classmethod
    def password_must_be_at_least_8_chars(cls, v):
        if len(v) < 8:
            raise ValueError('password must be at least 8 characters')
        return v


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
