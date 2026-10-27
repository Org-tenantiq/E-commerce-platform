from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

Base = declarative_base()

# Production database
engine = create_engine("sqlite:///./ecommerce.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_engine(database_url: str = "sqlite:///./ecommerce.db"):
    """Create a SQLAlchemy engine for the given database URL."""
    return create_engine(database_url, connect_args={"check_same_thread": False})
