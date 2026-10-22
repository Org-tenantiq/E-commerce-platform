import secrets
from datetime import datetime, timedelta, timezone

import pytest

PASSWORD = secrets.token_urlsafe(12)
A = {"email": "a@example.com", "password": PASSWORD}
B = {"email": "b@example.com", "password": PASSWORD}


@pytest.fixture(autouse=True)
def _jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", secrets.token_hex(32))


@pytest.fixture()
def now(monkeypatch):
    from api.app import clock

    state = {"t": datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)}
    monkeypatch.setattr(clock, "now", lambda: state["t"])
    return state


@pytest.fixture()
def users(client, now):
    for creds in (A, B):
        assert client.post("/auth/register", json=creds).status_code == 201


def _bad(client, email="a@example.com"):
    return client.post("/auth/login", json={"email": email, "password": "wrong-password-1"})


def test_sixth_attempt_throttled_even_with_right_password(client, users):
    for _ in range(5):
        assert _bad(client).status_code == 401
    r = client.post("/auth/login", json=A)
    assert r.status_code == 429
    retry = r.headers["retry-after"]
    assert retry.isdigit() and int(retry) > 0


def test_throttle_uses_normalised_email(client, users):
    for _ in range(5):
        assert _bad(client, " A@Example.com ").status_code == 401
    assert client.post("/auth/login", json=A).status_code == 429


def test_success_resets_failure_count(client, users):
    for _ in range(4):
        assert _bad(client).status_code == 401
    assert client.post("/auth/login", json=A).status_code == 200
    for _ in range(4):
        assert _bad(client).status_code == 401
    assert client.post("/auth/login", json=A).status_code == 200


def test_other_email_unaffected_and_window_expiry(client, users, now):
    for _ in range(5):
        _bad(client)
    assert client.post("/auth/login", json=B).status_code == 200
    assert client.post("/auth/login", json=A).status_code == 429
    now["t"] += timedelta(minutes=15, seconds=1)
    assert client.post("/auth/login", json=A).status_code == 200
