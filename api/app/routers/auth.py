"""Authentication routes."""
from __future__ import annotations

import jwt
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.app.db import get_db
from api.app.models import User
from api.app.config import (
    ACCESS_TOKEN_TTL_SECONDS,
    REFRESH_COOKIE_NAME,
    REFRESH_COOKIE_PATH,
    REFRESH_TOKEN_TTL_SECONDS,
)
from api.app.deps import _bearer, get_current_user
from api.app.passwords import hash_password, verify_password
from api.app.refresh import deny_access_token, issue_refresh_token, revoke_family, rotate_refresh_token
from api.app.schemas import LoginRequest, MeResponse, RegisterRequest, TokenResponse, UserRead
from api.app.tokens import create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

_CONFLICT = HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
_DUMMY_HASH = hash_password("dummy-password")


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        token,
        max_age=REFRESH_TOKEN_TTL_SECONDS,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=True,
        samesite="strict",
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    """Register a new customer account."""
    if db.scalar(select(User).where(User.email == payload.email)) is not None:
        raise _CONFLICT
    user = User(email=payload.email, password_hash=hash_password(payload.password), role="customer")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _CONFLICT
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    """Exchange credentials for an access token and a refresh cookie."""
    user = db.scalar(select(User).where(User.email == payload.email))
    # Always run a bcrypt check so unknown emails cost the same as wrong passwords.
    ok = verify_password(payload.password, user.password_hash if user else _DUMMY_HASH)
    if user is None or not ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _set_refresh_cookie(response, issue_refresh_token(db, user.id))
    return TokenResponse(
        access_token=create_access_token(user.id), expires_in=ACCESS_TOKEN_TTL_SECONDS
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Rotate the refresh token and return a new access token."""
    result = rotate_refresh_token(db, refresh_token) if refresh_token else None
    if result is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id, new_token = result
    _set_refresh_cookie(response, new_token)
    return TokenResponse(
        access_token=create_access_token(user_id), expires_in=ACCESS_TOKEN_TTL_SECONDS
    )


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)) -> User:
    """Return the authenticated caller."""
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> None:
    """End the session: revoke the refresh family, denylist the access token, clear the cookie."""
    if refresh_token:
        revoke_family(db, refresh_token)
    if creds is not None:
        try:
            claims = decode_access_token(creds.credentials)
            exp = datetime.fromtimestamp(claims["exp"], timezone.utc)
            deny_access_token(db, claims["jti"], exp)
        except (jwt.PyJWTError, ValueError, TypeError):
            pass  # already invalid; nothing to denylist
    response.delete_cookie(
        REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=True,
        samesite="strict",
    )
