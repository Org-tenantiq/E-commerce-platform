from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.app.schemas import RegisterRequest, UserResponse, LoginRequest, LoginResponse, CurrentUserResponse
from api.app.models import User
from api.app.passwords import hash_password, verify_password
from api.app.config import get_settings
from api.app.tokens import create_access_token
from api.app.deps import get_current_user

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


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Sign in with email and password."""
    email = req.email.lower().strip()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    settings = get_settings()
    token, expires_in = create_access_token(user.id, settings.jwt_secret)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in
    )


@router.get("/me", response_model=CurrentUserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the current user."""
    return current_user
