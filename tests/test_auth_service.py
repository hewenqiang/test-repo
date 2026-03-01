import pytest
from services.auth_service import (
    AuthService,
    AuthenticationError,
    InvalidCredentialsError,
    AccountDisabledError,
    ValidationError,
)
from models.user import User


@pytest.fixture
def auth_service():
    """Create a fresh AuthService instance for each test."""
    return AuthService()


@pytest.fixture
def auth_service_with_user(auth_service):
    """Create an AuthService with a pre-registered user."""
    auth_service.register("testuser", "SecurePass1", "test@example.com")
    return auth_service


# ==================== Registration Tests ====================

class TestRegistration:

    def test_register_success(self, auth_service):
        user = auth_service.register("john_doe", "mypassword", "john@example.com")
        assert user.username == "john_doe"
        assert user.email == "john@example.com"
        assert user.is_active is True
        assert user.user_id == 1

    def test_register_multiple_users(self, auth_service):
        user1 = auth_service.register("user1", "password1", "user1@example.com")
        user2 = auth_service.register("user2", "password2", "user2@example.com")
        assert user1.user_id == 1
        assert user2.user_id == 2

    def test_register_duplicate_username(self, auth_service_with_user):
        with pytest.raises(ValidationError, match="already taken"):
            auth_service_with_user.register("testuser", "AnotherPass1", "other@example.com")

    def test_register_duplicate_email(self, auth_service_with_user):
        with pytest.raises(ValidationError, match="already registered"):
            auth_service_with_user.register("newuser", "AnotherPass1", "test@example.com")

    def test_register_empty_username(self, auth_service):
        with pytest.raises(ValidationError, match="Username is required"):
            auth_service.register("", "password123", "test@example.com")

    def test_register_none_username(self, auth_service):
        with pytest.raises(ValidationError, match="Username is required"):
            auth_service.register(None, "password123", "test@example.com")

    def test_register_short_username(self, auth_service):
        with pytest.raises(ValidationError, match="at least 3 characters"):
            auth_service.register("ab", "password123", "test@example.com")

    def test_register_long_username(self, auth_service):
        with pytest.raises(ValidationError, match="must not exceed 50"):
            auth_service.register("a" * 51, "password123", "test@example.com")

    def test_register_invalid_username_chars(self, auth_service):
        with pytest.raises(ValidationError, match="letters, numbers, and underscores"):
            auth_service.register("user@name", "password123", "test@example.com")

    def test_register_username_with_spaces(self, auth_service):
        with pytest.raises(ValidationError, match="letters, numbers, and underscores"):
            auth_service.register("user name", "password123", "test@example.com")

    def test_register_empty_password(self, auth_service):
        with pytest.raises(ValidationError, match="Password is required"):
            auth_service.register("testuser", "", "test@example.com")

    def test_register_none_password(self, auth_service):
        with pytest.raises(ValidationError, match="Password is required"):
            auth_service.register("testuser", None, "test@example.com")

    def test_register_short_password(self, auth_service):
        with pytest.raises(ValidationError, match="at least 6 characters"):
            auth_service.register("testuser", "12345", "test@example.com")

    def test_register_long_password(self, auth_service):
        with pytest.raises(ValidationError, match="must not exceed 128"):
            auth_service.register("testuser", "a" * 129, "test@example.com")

    def test_register_invalid_email(self, auth_service):
        with pytest.raises(ValidationError, match="Invalid email"):
            auth_service.register("testuser", "password123", "not-an-email")

    def test_register_empty_email(self, auth_service):
        with pytest.raises(ValidationError, match="Email is required"):
            auth_service.register("testuser", "password123", "")

    def test_register_none_email(self, auth_service):
        with pytest.raises(ValidationError, match="Email is required"):
            auth_service.register("testuser", "password123", None)

    def test_register_email_normalized(self, auth_service):
        user = auth_service.register("testuser", "password123", "Test@Example.COM")
        assert user.email == "test@example.com"

    def test_register_username_trimmed(self, auth_service):
        user = auth_service.register("  testuser  ", "password123", "test@example.com")
        assert user.username == "testuser"

    def test_register_password_not_stored_plaintext(self, auth_service):
        user = auth_service.register("testuser", "password123", "test@example.com")
        assert user.password_hash != "password123"
        assert "$" in user.password_hash


# ==================== Login Tests ====================

class TestLogin:

    def test_login_success(self, auth_service_with_user):
        result = auth_service_with_user.login("testuser", "SecurePass1")
        assert result["success"] is True
        assert result["message"] == "Login successful."
        assert result["user"]["username"] == "testuser"
        assert result["user"]["email"] == "test@example.com"
        assert "session_token" in result
        assert len(result["session_token"]) > 0

    def test_login_returns_user_info(self, auth_service_with_user):
        result = auth_service_with_user.login("testuser", "SecurePass1")
        assert result["user"]["user_id"] == 1
        assert result["user"]["username"] == "testuser"
        assert result["user"]["email"] == "test@example.com"

    def test_login_updates_last_login(self, auth_service_with_user):
        user = auth_service_with_user.get_user("testuser")
        assert user.last_login is None
        auth_service_with_user.login("testuser", "SecurePass1")
        assert user.last_login is not None

    def test_login_wrong_password(self, auth_service_with_user):
        with pytest.raises(InvalidCredentialsError, match="Invalid username or password"):
            auth_service_with_user.login("testuser", "WrongPassword")

    def test_login_wrong_username(self, auth_service_with_user):
        with pytest.raises(InvalidCredentialsError, match="Invalid username or password"):
            auth_service_with_user.login("nonexistent", "SecurePass1")

    def test_login_empty_username(self, auth_service_with_user):
        with pytest.raises(ValidationError, match="Username is required"):
            auth_service_with_user.login("", "SecurePass1")

    def test_login_none_username(self, auth_service_with_user):
        with pytest.raises(ValidationError, match="Username is required"):
            auth_service_with_user.login(None, "SecurePass1")

    def test_login_empty_password(self, auth_service_with_user):
        with pytest.raises(ValidationError, match="Password is required"):
            auth_service_with_user.login("testuser", "")

    def test_login_none_password(self, auth_service_with_user):
        with pytest.raises(ValidationError, match="Password is required"):
            auth_service_with_user.login("testuser", None)

    def test_login_disabled_account(self, auth_service_with_user):
        auth_service_with_user.disable_user("testuser")
        with pytest.raises(AccountDisabledError, match="has been disabled"):
            auth_service_with_user.login("testuser", "SecurePass1")

    def test_login_generates_unique_tokens(self, auth_service_with_user):
        result1 = auth_service_with_user.login("testuser", "SecurePass1")
        result2 = auth_service_with_user.login("testuser", "SecurePass1")
        assert result1["session_token"] != result2["session_token"]

    def test_login_username_trimmed(self, auth_service_with_user):
        result = auth_service_with_user.login("  testuser  ", "SecurePass1")
        assert result["success"] is True


# ==================== Account Lockout Tests ====================

class TestAccountLockout:

    def test_failed_attempts_tracked(self, auth_service_with_user):
        for _ in range(3):
            with pytest.raises(InvalidCredentialsError):
                auth_service_with_user.login("testuser", "wrong")
        assert auth_service_with_user._failed_attempts["testuser"] == 3

    def test_account_locked_after_max_attempts(self, auth_service_with_user):
        # Exhaust all attempts
        for i in range(auth_service_with_user.MAX_FAILED_ATTEMPTS):
            try:
                auth_service_with_user.login("testuser", "wrong")
            except (InvalidCredentialsError, AccountDisabledError):
                pass

        # Next attempt should raise AccountDisabledError
        with pytest.raises(AccountDisabledError, match="locked"):
            auth_service_with_user.login("testuser", "SecurePass1")

    def test_successful_login_resets_failed_attempts(self, auth_service_with_user):
        # Fail a few times
        for _ in range(3):
            with pytest.raises(InvalidCredentialsError):
                auth_service_with_user.login("testuser", "wrong")
        assert auth_service_with_user._failed_attempts["testuser"] == 3

        # Successful login resets counter
        auth_service_with_user.login("testuser", "SecurePass1")
        assert auth_service_with_user._failed_attempts["testuser"] == 0

    def test_reset_failed_attempts(self, auth_service_with_user):
        for i in range(auth_service_with_user.MAX_FAILED_ATTEMPTS):
            try:
                auth_service_with_user.login("testuser", "wrong")
            except (InvalidCredentialsError, AccountDisabledError):
                pass

        auth_service_with_user.reset_failed_attempts("testuser")
        # Should be able to login now
        result = auth_service_with_user.login("testuser", "SecurePass1")
        assert result["success"] is True

    def test_failed_attempts_for_nonexistent_user(self, auth_service):
        with pytest.raises(InvalidCredentialsError):
            auth_service.login("ghost", "password")
        assert auth_service._failed_attempts.get("ghost") == 1


# ==================== Account Management Tests ====================

class TestAccountManagement:

    def test_disable_user(self, auth_service_with_user):
        auth_service_with_user.disable_user("testuser")
        user = auth_service_with_user.get_user("testuser")
        assert user.is_active is False

    def test_enable_user(self, auth_service_with_user):
        auth_service_with_user.disable_user("testuser")
        auth_service_with_user.enable_user("testuser")
        user = auth_service_with_user.get_user("testuser")
        assert user.is_active is True

    def test_enable_disabled_user_can_login(self, auth_service_with_user):
        auth_service_with_user.disable_user("testuser")
        auth_service_with_user.enable_user("testuser")
        result = auth_service_with_user.login("testuser", "SecurePass1")
        assert result["success"] is True

    def test_get_user_exists(self, auth_service_with_user):
        user = auth_service_with_user.get_user("testuser")
        assert user is not None
        assert user.username == "testuser"

    def test_get_user_not_exists(self, auth_service):
        user = auth_service.get_user("nonexistent")
        assert user is None

    def test_disable_nonexistent_user_no_error(self, auth_service):
        # Should not raise an error
        auth_service.disable_user("nonexistent")

    def test_enable_nonexistent_user_no_error(self, auth_service):
        # Should not raise an error
        auth_service.enable_user("nonexistent")


# ==================== Password Hashing Tests ====================

class TestPasswordHashing:

    def test_hash_password_produces_salt_and_hash(self):
        result, salt = AuthService._hash_password("mypassword")
        assert "$" in result
        assert len(salt) == 32  # 16 bytes hex = 32 chars

    def test_hash_password_different_salts(self):
        result1, _ = AuthService._hash_password("mypassword")
        result2, _ = AuthService._hash_password("mypassword")
        # Different salts should produce different hashes
        assert result1 != result2

    def test_hash_password_same_salt_same_result(self):
        result1, salt1 = AuthService._hash_password("mypassword")
        result2, salt2 = AuthService._hash_password("mypassword", salt1)
        assert result1 == result2

    def test_verify_password_correct(self):
        hashed, _ = AuthService._hash_password("mypassword")
        assert AuthService._verify_password("mypassword", hashed) is True

    def test_verify_password_incorrect(self):
        hashed, _ = AuthService._hash_password("mypassword")
        assert AuthService._verify_password("wrongpassword", hashed) is False

    def test_verify_password_malformed_hash(self):
        assert AuthService._verify_password("password", "nodoallarsign") is False


# ==================== User Model Tests ====================

class TestUserModel:

    def test_user_creation(self):
        user = User(
            user_id=1,
            username="testuser",
            password_hash="somehash",
            email="test@example.com",
        )
        assert user.user_id == 1
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.last_login is None

    def test_user_repr(self):
        user = User(
            user_id=1,
            username="testuser",
            password_hash="somehash",
            email="test@example.com",
        )
        repr_str = repr(user)
        assert "testuser" in repr_str
        assert "test@example.com" in repr_str
        assert "user_id=1" in repr_str


# ==================== Exception Hierarchy Tests ====================

class TestExceptions:

    def test_invalid_credentials_is_auth_error(self):
        assert issubclass(InvalidCredentialsError, AuthenticationError)

    def test_account_disabled_is_auth_error(self):
        assert issubclass(AccountDisabledError, AuthenticationError)

    def test_validation_error_is_auth_error(self):
        assert issubclass(ValidationError, AuthenticationError)


# ==================== Integration Tests ====================

class TestIntegration:

    def test_full_registration_and_login_flow(self, auth_service):
        # Register
        user = auth_service.register("alice", "alice_pass123", "alice@example.com")
        assert user.username == "alice"

        # Login
        result = auth_service.login("alice", "alice_pass123")
        assert result["success"] is True
        assert result["user"]["username"] == "alice"

    def test_multiple_users_independent_login(self, auth_service):
        auth_service.register("user_a", "pass_a_123", "a@example.com")
        auth_service.register("user_b", "pass_b_456", "b@example.com")

        result_a = auth_service.login("user_a", "pass_a_123")
        result_b = auth_service.login("user_b", "pass_b_456")

        assert result_a["user"]["username"] == "user_a"
        assert result_b["user"]["username"] == "user_b"

        # Cross-login should fail
        with pytest.raises(InvalidCredentialsError):
            auth_service.login("user_a", "pass_b_456")

    def test_register_login_disable_login_enable_login(self, auth_service):
        auth_service.register("bob", "bob_pass1", "bob@example.com")

        # Login works
        result = auth_service.login("bob", "bob_pass1")
        assert result["success"] is True

        # Disable account
        auth_service.disable_user("bob")
        with pytest.raises(AccountDisabledError):
            auth_service.login("bob", "bob_pass1")

        # Re-enable account
        auth_service.enable_user("bob")
        result = auth_service.login("bob", "bob_pass1")
        assert result["success"] is True