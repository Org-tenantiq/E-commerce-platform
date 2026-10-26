import pytest
import jwt
import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from api.app.models import User
from api.app.passwords import hash_password


class TestLoginAC1:
    """AC-1: Given correct credentials, return 200 with access_token, token_type "bearer", expires_in 900"""

    def test_login_returns_200_with_valid_credentials(self, client: TestClient, temp_db):
        """Test that login returns 200 with token info"""
        # First register a user
        email = "user@example.com"
        password = "ValidPassword123"
        client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )

        # Now login
        response = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_token_contains_required_claims(self, client: TestClient, temp_db):
        """Test that token contains sub, iat, exp, and jti claims"""
        # Get JWT_SECRET from environment
        jwt_secret = os.getenv("JWT_SECRET", "test-secret-key")

        # Register a user
        email = "test@example.com"
        password = "ValidPassword123"
        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )
        user_id = register_response.json()["id"]

        # Login
        response = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )
        token = response.json()["access_token"]

        # Decode token
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])

        # Check required claims
        assert "sub" in payload
        assert payload["sub"] == str(user_id)
        assert "iat" in payload
        assert "exp" in payload
        assert "jti" in payload
        assert isinstance(payload["jti"], str)
        assert len(payload["jti"]) > 0

    def test_login_token_expires_in_900_seconds(self, client: TestClient, temp_db):
        """Test that token expiration is 900 seconds after iat"""
        jwt_secret = os.getenv("JWT_SECRET", "test-secret-key")

        # Register and login
        email = "test@example.com"
        password = "ValidPassword123"
        client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )
        response = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )
        token = response.json()["access_token"]

        # Decode token
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])

        # Check expiration is 900 seconds after iat
        assert payload["exp"] - payload["iat"] == 900

    def test_login_token_jti_is_unique(self, client: TestClient, temp_db):
        """Test that each token has a unique jti"""
        jwt_secret = os.getenv("JWT_SECRET", "test-secret-key")

        email = "test@example.com"
        password = "ValidPassword123"
        client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )

        # Get two tokens
        response1 = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )
        token1 = response1.json()["access_token"]

        response2 = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )
        token2 = response2.json()["access_token"]

        # Decode both tokens
        payload1 = jwt.decode(token1, jwt_secret, algorithms=["HS256"])
        payload2 = jwt.decode(token2, jwt_secret, algorithms=["HS256"])

        # Check jti is different
        assert payload1["jti"] != payload2["jti"]


class TestLoginAC2:
    """AC-2: Given wrong password or unknown email, both return 401 with identical body"""

    def test_login_unknown_email_returns_401(self, client: TestClient):
        """Test that unknown email returns 401"""
        response = client.post(
            "/auth/login",
            json={"email": "unknown@example.com", "password": "SomePassword123"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    def test_login_wrong_password_returns_401(self, client: TestClient):
        """Test that wrong password returns 401"""
        email = "test@example.com"
        password = "ValidPassword123"
        client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )

        response = client.post(
            "/auth/login",
            json={"email": email, "password": "WrongPassword123"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    def test_login_unknown_email_and_wrong_password_identical_response(self, client: TestClient):
        """Test that unknown email and wrong password return identical responses"""
        # Register a user
        email = "registered@example.com"
        password = "ValidPassword123"
        client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )

        # Try unknown email
        response_unknown = client.post(
            "/auth/login",
            json={"email": "unknown@example.com", "password": "SomePassword123"}
        )

        # Try wrong password
        response_wrong_password = client.post(
            "/auth/login",
            json={"email": email, "password": "WrongPassword123"}
        )

        # Both should return 401 with identical body
        assert response_unknown.status_code == 401
        assert response_wrong_password.status_code == 401
        assert response_unknown.json() == response_wrong_password.json()

    def test_login_email_case_insensitive(self, client: TestClient):
        """Test that email is case-insensitive for login"""
        email = "User@Example.COM"
        password = "ValidPassword123"
        client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )

        # Login with different case
        response = client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": password}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestLoginAC3:
    """AC-3: Given GET /me, valid bearer token returns user, invalid/missing token returns 401 with WWW-Authenticate: Bearer"""

    def test_me_with_valid_token_returns_200(self, client: TestClient):
        """Test that GET /me with valid token returns 200 with user info"""
        email = "test@example.com"
        password = "ValidPassword123"
        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )
        user_id = register_response.json()["id"]
        role = register_response.json()["role"]

        # Login to get token
        login_response = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )
        token = login_response.json()["access_token"]

        # Call GET /me with token
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == email
        assert data["role"] == role

    def test_me_without_token_returns_401_with_www_authenticate(self, client: TestClient):
        """Test that GET /me without token returns 401 with WWW-Authenticate header"""
        response = client.get("/auth/me")
        assert response.status_code == 401
        assert "www-authenticate" in response.headers or "WWW-Authenticate" in response.headers

    def test_me_with_malformed_token_returns_401_with_www_authenticate(self, client: TestClient):
        """Test that malformed token returns 401 with WWW-Authenticate header"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer malformed-token"}
        )
        assert response.status_code == 401
        assert "www-authenticate" in response.headers or "WWW-Authenticate" in response.headers

    def test_me_with_expired_token_returns_401_with_www_authenticate(self, client: TestClient):
        """Test that expired token returns 401 with WWW-Authenticate header"""
        import time
        jwt_secret = os.getenv("JWT_SECRET", "test-secret-key")

        # Create an expired token manually
        import uuid
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        expired_payload = {
            "sub": "1",
            "iat": int((now - timedelta(seconds=1000)).timestamp()),
            "exp": int((now - timedelta(seconds=100)).timestamp()),
            "jti": str(uuid.uuid4()),
        }
        expired_token = jwt.encode(expired_payload, jwt_secret, algorithm="HS256")

        # Try to use expired token
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
        assert "www-authenticate" in response.headers or "WWW-Authenticate" in response.headers

    def test_me_with_wrong_secret_returns_401_with_www_authenticate(self, client: TestClient):
        """Test that token signed with wrong key returns 401 with WWW-Authenticate header"""
        import uuid
        from datetime import datetime, timedelta

        # Create token with a different secret
        wrong_secret = "wrong-secret-key"
        now = datetime.utcnow()
        payload = {
            "sub": "1",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=900)).timestamp()),
            "jti": str(uuid.uuid4()),
        }
        wrong_token = jwt.encode(payload, wrong_secret, algorithm="HS256")

        # Try to use token with wrong secret
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {wrong_token}"}
        )
        assert response.status_code == 401
        assert "www-authenticate" in response.headers or "WWW-Authenticate" in response.headers

    def test_me_returns_correct_user_data_structure(self, client: TestClient):
        """Test that GET /me returns only id, email, and role"""
        email = "test@example.com"
        password = "ValidPassword123"
        register_response = client.post(
            "/auth/register",
            json={"email": email, "password": password}
        )
        user_id = register_response.json()["id"]

        # Login to get token
        login_response = client.post(
            "/auth/login",
            json={"email": email, "password": password}
        )
        token = login_response.json()["access_token"]

        # Call GET /me with token
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        # Check that only expected fields are present
        assert set(data.keys()) == {"id", "email", "role"}
        assert data["id"] == user_id
        assert data["email"] == email
