"""Environment-based settings. JWT_SECRET has no default and is validated at startup."""
from __future__ import annotations

import os

MIN_JWT_SECRET_LENGTH = 32
ACCESS_TOKEN_TTL_SECONDS = 900
JWT_ALGORITHM = "HS256"


def get_jwt_secret() -> str:
    """Return JWT_SECRET, raising RuntimeError if unset or too short."""
    secret = os.environ.get("JWT_SECRET", "")
    if len(secret) < MIN_JWT_SECRET_LENGTH:
        raise RuntimeError(
            f"JWT_SECRET must be set to at least {MIN_JWT_SECRET_LENGTH} characters"
        )
    return secret

REFRESH_TOKEN_TTL_SECONDS = 604800
REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/auth"
