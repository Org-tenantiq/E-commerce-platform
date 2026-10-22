"""Shared FastAPI dependencies."""
from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from api.app.db import get_db
from api.app.models import RevokedToken, User
from api.app.tokens import decode_access_token

_bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the caller from the bearer token or raise 401."""
    if creds is None:
        raise _unauthorized()
    try:
        claims = decode_access_token(creds.credentials)
        user_id = int(claims["sub"])
    except (jwt.PyJWTError, ValueError):
        raise _unauthorized()
    if db.get(RevokedToken, claims["jti"]) is not None:
        raise _unauthorized()
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized()
    return user
