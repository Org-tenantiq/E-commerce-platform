from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.app.schemas import RegisterRequest, UserResponse
from api.app.models import User
from api.app.passwords import hash_password

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    from api.app.db import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user with email and password."""
    try:
        # Normalize email: lowercase and trim
        email = req.email.lower().strip()

        # Hash the password
        password_hash = hash_password(req.password)

        # Create new user
        user = User(email=email, password_hash=password_hash, role="customer")
        db.add(user)
        db.commit()
        db.refresh(user)

        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    except ValueError as e:
        # Password validation error from hash_password
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
