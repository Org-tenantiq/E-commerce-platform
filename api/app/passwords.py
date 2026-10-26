import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with cost 12.

    Args:
        password: The plain text password to hash

    Returns:
        A bcrypt hash string starting with $2b$

    Raises:
        ValueError: If password is less than 8 characters or more than 72 bytes
    """
    password_bytes = password.encode('utf-8')

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    if len(password_bytes) > 72:
        raise ValueError("Password must not exceed 72 bytes in UTF-8")

    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash.

    Args:
        password: The plain text password to verify
        hashed: The bcrypt hash to verify against

    Returns:
        True if password matches the hash, False otherwise
        Never raises, even for malformed hashes
    """
    try:
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False
