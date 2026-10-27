import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set JWT_SECRET for tests if not already set
if not os.getenv("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-secret-key-for-testing"

from api.app.main import app

# Try to import database components - if they don't exist, tests will fail naturally
# when they try to use the missing endpoints
Base = None
get_db_auth = None
get_db_deps = None

try:
    from api.app.db import Base
    from api.app.routers.auth import get_db as get_db_auth
    from api.app.deps import get_db as get_db_deps
except ImportError:
    pass


@pytest.fixture(scope="function")
def temp_db():
    """Create a temporary SQLite database for testing."""
    if Base is None:
        # If database components are not available, yield None and let tests fail naturally
        yield None
        return

    # Create a temporary file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Create engine with temp db
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Override the get_db dependency
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    if get_db_auth is not None:
        app.dependency_overrides[get_db_auth] = override_get_db
    if get_db_deps is not None:
        app.dependency_overrides[get_db_deps] = override_get_db

    yield engine

    # Cleanup
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    os.unlink(db_path)


@pytest.fixture
def client(temp_db):
    """Create a test client with temporary database."""
    return TestClient(app)
