import secrets
import time

import jwt
import pytest

from api.app.main import app

SECRET = secrets.token_hex(32)
OTHER_KEY = secrets.token_hex(32)
CREDS = {"email": "a@example.com", "password": secrets.token_urlsafe(12)}


@pytest.fixture(autouse=True)
def _jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)


@pytest.fixture()
def registered(client):
    assert client.post("/auth/register", json=CREDS).status_code == 201


def _token(client):
    return client.post("/auth/login", json=CREDS).json()["access_token"]


def test_login_success(client, registered):
    r = client.post("/auth/login", json=CREDS)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and body["expires_in"] == 900
    claims = jwt.decode(body["access_token"], SECRET, algorithms=["HS256"])
    assert claims["sub"].isdigit()
    assert claims["exp"] - claims["iat"] == 900
    assert claims["jti"] != jwt.decode(_token(client), SECRET, algorithms=["HS256"])["jti"]


def test_login_failures_identical(client, registered):
    bad_pw = client.post("/auth/login", json={**CREDS, "password": "wrong-password"})
    unknown = client.post("/auth/login", json={**CREDS, "email": "x@example.com"})
    assert bad_pw.status_code == unknown.status_code == 401
    assert bad_pw.json() == unknown.json() == {"detail": "Invalid email or password"}
    assert bad_pw.headers["WWW-Authenticate"] == "Bearer"


def test_me_valid(client, registered):
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {_token(client)}"})
    assert r.status_code == 200
    assert r.json()["email"] == CREDS["email"] and r.json()["role"] == "customer"
    assert "id" in r.json()


def _forged(key, alg="HS256", **over):
    now = int(time.time())
    claims = {"sub": "1", "iat": now, "exp": now + 900, "jti": "x", **over}
    return jwt.encode(claims, key, algorithm=alg)


def test_me_rejects_bad_tokens(client, registered):
    now = int(time.time())
    tokens = [
        "garbage",
        _forged(SECRET, iat=now - 2000, exp=now - 1000),
        _forged(OTHER_KEY),
    ]
    none_token = jwt.encode({"sub": "1", "iat": now, "exp": now + 900, "jti": "x"}, None, algorithm="none")
    tokens.append(none_token)
    for t in tokens:
        r = client.get("/auth/me", headers={"Authorization": f"Bearer {t}"})
        assert r.status_code == 401
        assert r.headers["WWW-Authenticate"] == "Bearer"
    r = client.get("/auth/me")
    assert r.status_code == 401 and r.headers["WWW-Authenticate"] == "Bearer"


def test_startup_requires_jwt_secret(monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.delenv("JWT_SECRET")
    with pytest.raises(RuntimeError):
        with TestClient(app):
            pass
