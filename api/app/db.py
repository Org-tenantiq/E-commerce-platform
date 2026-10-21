"""SQLAlchemy 2.0 engine, session factory and FastAPI session dependency."""
from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def init_db() -> None:
    """Create all tables if they do not exist."""
    from api.app import models  # noqa: F401  (register models)

    Base.metadata.create_all(engine)


def get_db() -> Iterator[Session]:
    """Yield a database session and close it afterwards."""
    with SessionLocal() as session:
        yield session
