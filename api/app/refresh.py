"""Refresh token issuing and rotation. Only SHA-256 hex digests are stored."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from api.app.config import REFRESH_TOKEN_TTL_SECONDS
from api.app.models import RefreshToken, RevokedToken


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _new(db: Session, user_id: int, family_id: str) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(seconds=REFRESH_TOKEN_TTL_SECONDS)
    db.add(
        RefreshToken(
            user_id=user_id, family_id=family_id, token_hash=hash_token(token), expires_at=expires
        )
    )
    return token


def issue_refresh_token(db: Session, user_id: int) -> str:
    """Start a new token family and return the raw token."""
    token = _new(db, user_id, secrets.token_hex(16))
    db.commit()
    return token


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def rotate_refresh_token(db: Session, token: str) -> tuple[int, str] | None:
    """Return (user_id, new_token), or None if invalid. Reuse revokes the whole family."""
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(token)))
    if row is None:
        return None
    now = datetime.now(timezone.utc)
    if row.used_at is not None or row.revoked_at is not None:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == row.family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.commit()
        return None
    if _aware(row.expires_at) <= now:
        return None
    row.used_at = now
    new_token = _new(db, row.user_id, row.family_id)
    db.commit()
    return row.user_id, new_token


def revoke_family(db: Session, token: str) -> None:
    """Revoke every token in the family of the given refresh token; unknown tokens are a no-op."""
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(token)))
    if row is None:
        return
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == row.family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    db.commit()


def deny_access_token(db: Session, jti: str, expires_at: datetime) -> None:
    """Denylist a jti until its exp and purge rows whose tokens have already expired."""
    db.execute(delete(RevokedToken).where(RevokedToken.expires_at <= datetime.now(timezone.utc)))
    if db.get(RevokedToken, jti) is None:
        db.add(RevokedToken(jti=jti, expires_at=expires_at))
    db.commit()
