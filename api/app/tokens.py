"""Access token creation and verification (HS256)."""
from __future__ import annotations

import time
import uuid

import jwt

from api.app.config import ACCESS_TOKEN_TTL_SECONDS, JWT_ALGORITHM, get_jwt_secret


def create_access_token(user_id: int) -> str:
    """Issue a signed token for the user, valid for ACCESS_TOKEN_TTL_SECONDS."""
    now = int(time.time())
    claims = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL_SECONDS,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(claims, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a token; raises jwt.PyJWTError on any failure."""
    return jwt.decode(
        token,
        get_jwt_secret(),
        algorithms=[JWT_ALGORITHM],
        options={"require": ["sub", "iat", "exp", "jti"]},
    )
