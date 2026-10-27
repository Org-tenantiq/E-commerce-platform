import pytest
from api.app.passwords import hash_password, verify_password


class TestHashPassword:
    """AC-2: hash_password returns bcrypt hash and verify_password works"""

    def test_hash_password_returns_bcrypt_hash(self):
        password = "ValidPassword123"
        hashed = hash_password(password)
        assert hashed.startswith("$2b$")
        assert hashed != password

    def test_verify_password_returns_true_for_correct_password(self):
        password = "ValidPassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_returns_false_for_wrong_password(self):
        password = "ValidPassword123"
        wrong_password = "WrongPassword456"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_handles_malformed_hash(self):
        password = "ValidPassword123"
        malformed_hash = "not_a_valid_hash"
        # Should not raise, should return False
        result = verify_password(password, malformed_hash)
        assert result is False


class TestPasswordValidation:
    """AC-3: Passwords outside 8-72 bytes range raise ValueError"""

    def test_hash_password_raises_for_password_under_8_characters(self):
        password = "Short1"  # 6 characters
        with pytest.raises(ValueError):
            hash_password(password)

    def test_hash_password_raises_for_password_over_72_bytes(self):
        password = "a" * 73  # 73 bytes
        with pytest.raises(ValueError):
            hash_password(password)

    def test_hash_password_accepts_exactly_8_characters(self):
        password = "Valid123"  # exactly 8 characters
        hashed = hash_password(password)
        assert hashed.startswith("$2b$")

    def test_hash_password_accepts_exactly_72_bytes(self):
        password = "a" * 72  # exactly 72 bytes
        hashed = hash_password(password)
        assert hashed.startswith("$2b$")
