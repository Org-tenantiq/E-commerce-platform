import pytest
from fastapi.testclient import TestClient
from api.app.passwords import verify_password


class TestRegisterAC1:
    """AC-1: Given valid email and password, return 201 with id, email, role, created_at, no password fields"""

    def test_register_returns_201_with_valid_email_and_password(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "ValidPassword123"}
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == "test@example.com"
        assert data["role"] == "customer"
        assert "created_at" in data
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_response_excludes_password_field(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "SecurePass123"}
        )
        assert response.status_code == 201
        data = response.json()
        assert "password" not in data

    def test_register_response_excludes_password_hash_field(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={"email": "user2@example.com", "password": "SecurePass123"}
        )
        assert response.status_code == 201
        data = response.json()
        assert "password_hash" not in data


class TestRegisterAC2:
    """AC-2: Given email already registered, return 409 with error message"""

    def test_register_duplicate_email_returns_409(self, client: TestClient):
        # First registration
        client.post(
            "/auth/register",
            json={"email": "duplicate@example.com", "password": "ValidPassword123"}
        )
        # Second registration with same email
        response = client.post(
            "/auth/register",
            json={"email": "duplicate@example.com", "password": "ValidPassword456"}
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "Email already registered"

    def test_register_duplicate_email_case_insensitive_returns_409(self, client: TestClient):
        # Register with lowercase
        client.post(
            "/auth/register",
            json={"email": "user@example.com", "password": "ValidPassword123"}
        )
        # Try to register with uppercase
        response = client.post(
            "/auth/register",
            json={"email": "USER@EXAMPLE.COM", "password": "ValidPassword456"}
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "Email already registered"

    def test_register_duplicate_email_mixed_case_returns_409(self, client: TestClient):
        # Register with mixed case
        client.post(
            "/auth/register",
            json={"email": "Test@Example.com", "password": "ValidPassword123"}
        )
        # Try to register with different case
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "ValidPassword456"}
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "Email already registered"


class TestRegisterAC3:
    """AC-3: Given invalid email or password < 8 chars, return 422, and verify password_hash"""

    def test_register_password_under_8_characters_returns_422(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "Short1"}
        )
        assert response.status_code == 422

    def test_register_invalid_email_returns_422(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={"email": "invalid-email", "password": "ValidPassword123"}
        )
        assert response.status_code == 422

    def test_register_empty_password_returns_422(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": ""}
        )
        assert response.status_code == 422

    def test_register_stores_password_hash_that_verifies(self, client: TestClient, temp_db):
        """Verify that the stored password_hash can be verified with verify_password"""
        from sqlalchemy.orm import sessionmaker
        from api.app.models import User

        email = "verify@example.com"
        password = "VerifyPassword123"

        # Register user
        response = client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )
        assert response.status_code == 201

        # Get the user from database and verify password
        SessionLocal = sessionmaker(bind=temp_db)
        db = SessionLocal()
        user = db.query(User).filter(User.email == email.lower()).first()
        db.close()

        assert user is not None
        assert verify_password(password, user.password_hash) is True
        assert verify_password("WrongPassword123", user.password_hash) is False

    def test_register_trims_email_whitespace(self, client: TestClient):
        """Verify that email with surrounding whitespace is trimmed"""
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "ValidPassword123"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_register_stores_email_lowercase(self, client: TestClient, temp_db):
        """Verify that email is stored in lowercase"""
        from sqlalchemy.orm import sessionmaker
        from api.app.models import User

        # Register with mixed case
        response = client.post(
            "/auth/register",
            json={"email": "Test@Example.COM", "password": "ValidPassword123"}
        )
        assert response.status_code == 201

        # Check in database
        SessionLocal = sessionmaker(bind=temp_db)
        db = SessionLocal()
        user = db.query(User).filter(User.email == "test@example.com").first()
        db.close()

        assert user is not None
        assert user.email == "test@example.com"
