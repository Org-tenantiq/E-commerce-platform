"""Authentication routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.app.db import get_db
from api.app.models import User
from api.app.passwords import hash_password
from api.app.schemas import RegisterRequest, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

_CONFLICT = HTTPException(status.HTTP_409_CONFLICT, "Email already registered")


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
