import secrets
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

CREDS = {"email": "l@example.com", "password": secrets.token_urlsafe(12)}


@pytest.fixture(autouse=True)
def _jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", secrets.token_hex(32))


@pytest.fixture()
def session(client):
    assert client.post("/auth/register", json=CREDS).status_code == 201
    client.cookies.clear()
    r = client.post("/auth/login", json=CREDS)
    client.cookies.clear()
    cookie = r.headers["set-cookie"].split(";", 1)[0].split("=", 1)[1]
    return r.json()["access_token"], cookie


def _logout(client, access=None, cookie=None):
    headers = {}
    if access:
        headers["Authorization"] = f"Bearer {access}"
    if cookie:
        headers["Cookie"] = f"refresh_token={cookie}"
    return client.post("/auth/logout", headers=headers)


def test_logout_revokes_family_and_clears_cookie(client, session, session_factory):
    from api.app.models import RefreshToken

    access, cookie = session
    r = _logout(client, access, cookie)
    assert r.status_code == 204
    sc = r.headers["set-cookie"].lower()
    assert "max-age=0" in sc and "path=/auth" in sc
    with session_factory() as s:
        rows = s.scalars(select(RefreshToken)).all()
        assert rows and all(row.revoked_at is not None for row in rows)
    client.cookies.clear()
    assert client.post("/auth/refresh", headers={"Cookie": f"refresh_token={cookie}"}).status_code == 401


def test_access_token_rejected_after_logout(client, session):
    access, cookie = session
    auth = {"Authorization": f"Bearer {access}"}
    assert client.get("/auth/me", headers=auth).status_code == 200
    _logout(client, access, cookie)
    assert client.get("/auth/me", headers=auth).status_code == 401


def test_logout_without_credentials_is_204(client):
    assert _logout(client).status_code == 204


def test_logout_is_idempotent(client, session):
    access, cookie = session
    assert _logout(client, access, cookie).status_code == 204
    assert _logout(client, access, cookie).status_code == 204


def test_logout_with_garbage_tokens_is_204(client):
    assert _logout(client, "not.a.jwt", "bogus").status_code == 204


def test_expired_denylist_rows_purged(client, session, session_factory):
    from api.app.models import RevokedToken

    with session_factory() as s:
        s.add(RevokedToken(jti="old", expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
        s.commit()
    access, cookie = session
    _logout(client, access, cookie)
    with session_factory() as s:
        jtis = {r.jti for r in s.scalars(select(RevokedToken))}
    assert "old" not in jtis and len(jtis) == 1
