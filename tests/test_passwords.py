import pytest
from api.app.passwords import (
    hash_password,
    verify_password,
    MIN_PASSWORD_LENGTH,
    MAX_PASSWORD_BYTES,
)


def test_AC_2_1_hash_returns_bcrypt_prefix():
    """AC-2.1: hash_password returns a bcrypt hash starting with '$2b$' and differs from the input"""
    password = "correcthorsebatterystaple"
    # sanity check the example meets the MIN_PASSWORD_LENGTH requirement
    assert len(password) >= MIN_PASSWORD_LENGTH

    pw_hash = hash_password(password)
    assert isinstance(pw_hash, str)
    assert pw_hash.startswith("$2b$")
    assert pw_hash != password


def test_AC_2_2_verify_true_and_false():
    """AC-2.2: verify_password returns True for the correct password and False for an incorrect one"""
    password = "correcthorsebatterystaple"
    pw_hash = hash_password(password)

    assert verify_password(password, pw_hash) is True
    assert verify_password("wrong", pw_hash) is False


def test_AC_3_1_short_password_raises():
    """AC-3.1: passwords shorter than MIN_PASSWORD_LENGTH raise ValueError"""
    short_pw = "short"
    # ensure the test input is indeed shorter than the module's MIN_PASSWORD_LENGTH
    assert len(short_pw) < MIN_PASSWORD_LENGTH

    with pytest.raises(ValueError):
        hash_password(short_pw)


def test_AC_3_2_too_long_bytes_raises():
    """AC-3.2: passwords whose UTF-8 encoding is longer than MAX_PASSWORD_BYTES raise ValueError"""
    long_pw = "a" * (MAX_PASSWORD_BYTES + 1)
    # ensure the encoded length exceeds MAX_PASSWORD_BYTES
    assert len(long_pw.encode("utf-8")) > MAX_PASSWORD_BYTES

    with pytest.raises(ValueError):
        hash_password(long_pw)
