"""Password hashing and verification helpers using bcrypt.

This module intentionally uses the `bcrypt` package directly rather than a
higher-level wrapper to ensure predictable behavior with bcrypt 4.x.

Public constants:
- MIN_PASSWORD_LENGTH: minimum number of characters accepted for a password
- MAX_PASSWORD_BYTES: maximum number of bytes allowed after UTF-8 encoding

Public functions:
- hash_password(password: str) -> str
- verify_password(password: str, password_hash: str) -> bool
"""
from __future__ import annotations

from typing import Final

import bcrypt


MIN_PASSWORD_LENGTH: Final[int] = 8
MAX_PASSWORD_BYTES: Final[int] = 72


def _validate_password_bytes(password: str) -> bytes:
    """Encode the password to UTF-8 and validate its length in bytes.

    Raises ValueError if the password encoded bytes are shorter than
    MIN_PASSWORD_LENGTH or longer than MAX_PASSWORD_BYTES.
    """
    if not isinstance(password, str):
        raise TypeError("password must be a string")

    raw = password.encode("utf-8")
    length = len(raw)
    if length < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"password must be at least {MIN_PASSWORD_LENGTH} characters"
        )
    if length > MAX_PASSWORD_BYTES:
        raise ValueError(
            f"password must be at most {MAX_PASSWORD_BYTES} bytes when UTF-8 encoded"
        )
    return raw


def hash_password(password: str) -> str:
    """Hash a password using bcrypt and return the ASCII-encoded hash string.

    The function validates the password length and raises ValueError for
    passwords that are too short or that would be silently truncated by
    bcrypt because they exceed MAX_PASSWORD_BYTES.

    Args:
        password: the plaintext password to hash.

    Returns:
        A bcrypt hash string (ASCII), e.g. starting with "$2b$".

    Raises:
        ValueError: if the password is too short or too long in UTF-8 bytes.
        TypeError: if password is not a str.
    """
    raw = _validate_password_bytes(password)
    hashed = bcrypt.hashpw(raw, bcrypt.gensalt(rounds=12))
    # bcrypt.hashpw returns bytes; decode to ASCII for storage/transport
    return hashed.decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    The function returns False for an incorrect password or for malformed
    hashes. It never raises for those normal failure cases.

    Args:
        password: plaintext password to verify.
        password_hash: the bcrypt hash string to verify against.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    if not password:
        return False
    if not isinstance(password_hash, str):
        return False

    try:
        raw = password.encode("utf-8")
        hashed = password_hash.encode("ascii")
    except Exception:
        # Encoding errors or similar -> treat as non-match
        return False

    try:
        return bcrypt.checkpw(raw, hashed)
    except (ValueError, TypeError):
        # bcrypt raises ValueError on malformed hashes; treat as non-match
        return False
