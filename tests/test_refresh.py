import hashlib
import secrets

import pytest
from sqlalchemy import select

CREDS = {"email": "r@example.com", "password": secrets.token_urlsafe(12)}


@pytest.fixture(autouse=True)
def _jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", secrets.token_hex(32))


@pytest.fixture()
def registered(client):
    assert client.post("/auth/register", json=CREDS).status_code == 201


def _login(client):
    client.cookies.clear()
    return client.post("/auth/login", json=CREDS)


def _cookie_value(resp):
    header = resp.headers["set-cookie"]
    return header.split(";", 1)[0].split("=", 1)[1]


def _refresh(client, token):
    client.cookies.clear()
    # Secure cookies are not replayed over http, so send the cookie explicitly.
    return client.post("/auth/refresh", headers={"Cookie": f"refresh_token={token}"})


def test_login_sets_cookie_and_stores_hash(client, registered, session_factory):
    from api.app.models import RefreshToken

    r = _login(client)
    assert r.status_code == 200
    header = r.headers["set-cookie"]
    assert header.startswith("refresh_token=")
    low = header.lower()
    for flag in ("httponly", "secure", "samesite=strict", "path=/auth", "max-age=604800"):
        assert flag in low
    token = _cookie_value(r)
    with session_factory() as s:
        rows = s.scalars(select(RefreshToken)).all()
    assert len(rows) == 1
    assert rows[0].token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert token not in repr([getattr(rows[0], c.name) for c in RefreshToken.__table__.columns])


def test_refresh_rotates(client, registered, session_factory):
    from api.app.models import RefreshToken

    old = _cookie_value(_login(client))
    r = _refresh(client, old)
    assert r.status_code == 200
    assert r.json()["access_token"]
    new = _cookie_value(r)
    assert new != old
    assert "httponly" in r.headers["set-cookie"].lower()
    with session_factory() as s:
        used = {
            t.token_hash: t.used_at for t in s.scalars(select(RefreshToken)).all()
        }
    assert used[hashlib.sha256(old.encode()).hexdigest()] is not None
    assert used[hashlib.sha256(new.encode()).hexdigest()] is None


def test_reuse_revokes_family(client, registered):
    old = _cookie_value(_login(client))
    newest = _cookie_value(_refresh(client, old))
    assert _refresh(client, old).status_code == 401
    assert _refresh(client, newest).status_code == 401


def test_missing_or_unknown_cookie(client, registered):
    client.cookies.clear()
    assert client.post("/auth/refresh").status_code == 401
    assert _refresh(client, "nope").status_code == 401
