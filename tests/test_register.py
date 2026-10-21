import pytest

from api.app.models import User
from api.app.passwords import verify_password

PW = "correct-horse"


def test_AC_1_register_returns_201_without_password(client):
    r = client.post("/auth/register", json={"email": "a@example.com", "password": PW})
    assert r.status_code == 201
    body = r.json()
    assert set(body) == {"id", "email", "role", "created_at"}
    assert body["email"] == "a@example.com"
    assert body["role"] == "customer"


@pytest.mark.parametrize("email", ["A@Example.com", "  a@example.com ", " A@EXAMPLE.COM"])
def test_AC_2_duplicate_email_409(client, email):
    assert client.post("/auth/register", json={"email": "a@example.com", "password": PW}).status_code == 201
    r = client.post("/auth/register", json={"email": email, "password": PW})
    assert r.status_code == 409
    assert r.json() == {"detail": "Email already registered"}


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email", "password": PW},
        {"email": "a@example.com", "password": "short"},
        {"email": "a@example.com", "password": "x" * 73},
        {"email": "a@example.com"},
    ],
)
def test_AC_3_invalid_input_422(client, payload):
    assert client.post("/auth/register", json=payload).status_code == 422


def test_AC_3_stored_hash_verifies(client, session_factory):
    client.post("/auth/register", json={"email": "A@example.com", "password": PW})
    with session_factory() as s:
        user = s.query(User).one()
    assert user.email == "a@example.com"
    assert user.password_hash != PW
    assert verify_password(PW, user.password_hash)
