import jwt
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

TOKEN_EXPIRY_SECONDS = 900


def create_access_token(user_id: int, secret: str) -> tuple[str, int]:
    """Create an HS256 JWT access token.

    Returns:
        tuple of (token, expires_in_seconds)
    """
    now = datetime.utcnow()
    expires_in = TOKEN_EXPIRY_SECONDS
    expiration = now + timedelta(seconds=expires_in)

    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expiration.timestamp()),
        "jti": str(uuid.uuid4()),
    }

    token = jwt.encode(payload, secret, algorithm="HS256")
    return token, expires_in


def decode_access_token(token: str, secret: str) -> Optional[Dict[str, Any]]:
    """Decode an HS256 JWT access token.

    Returns:
        Decoded payload if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.DecodeError):
        return None
