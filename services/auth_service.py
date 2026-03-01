import hashlib
import secrets
import re
from datetime import datetime
from typing import Optional, Dict, Tuple

from models.user import User


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when username or password is incorrect."""
    pass


class AccountDisabledError(AuthenticationError):
    """Raised when the user account is disabled."""
    pass


class ValidationError(AuthenticationError):
    """Raised when input validation fails."""
    pass


class AuthService:
    """
    Authentication service handling user registration and login.
    Uses SHA-256 with salt for password hashing.
    """

    def __init__(self):
        # In-memory user store: username -> User
        self._users: Dict[str, User] = {}
        self._next_id: int = 1
        # Track failed login attempts: username -> count
        self._failed_attempts: Dict[str, int] = {}
        self.MAX_FAILED_ATTEMPTS = 5

    @staticmethod
    def _hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash a password with a salt using SHA-256.
        Returns (hashed_password, salt) tuple.
        """
        if salt is None:
            salt = secrets.token_hex(16)
        hashed = hashlib.sha256(f"{salt}{password}".encode('utf-8')).hexdigest()
        return f"{salt}${hashed}", salt

    @staticmethod
    def _verify_password(password: str, stored_hash: str) -> bool:
        """Verify a password against a stored hash."""
        try:
            salt, expected_hash = stored_hash.split('$', 1)
        except ValueError:
            return False
        actual_hash = hashlib.sha256(f"{salt}{password}".encode('utf-8')).hexdigest()
        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(actual_hash, expected_hash)

    @staticmethod
    def _validate_username(username: str) -> None:
        """Validate username format."""
        if not username or not isinstance(username, str):
            raise ValidationError("Username is required and must be a string.")
        username = username.strip()
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        if len(username) > 50:
            raise ValidationError("Username must not exceed 50 characters.")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")

    @staticmethod
    def _validate_password(password: str) -> None:
        """Validate password strength."""
        if not password or not isinstance(password, str):
            raise ValidationError("Password is required and must be a string.")
        if len(password) < 6:
            raise ValidationError("Password must be at least 6 characters long.")
        if len(password) > 128:
            raise ValidationError("Password must not exceed 128 characters.")

    @staticmethod
    def _validate_email(email: str) -> None:
        """Validate email format."""
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required and must be a string.")
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.strip()):
            raise ValidationError("Invalid email format.")

    def register(self, username: str, password: str, email: str) -> User:
        """
        Register a new user.

        Args:
            username: The desired username (3-50 chars, alphanumeric + underscore)
            password: The password (min 6 chars)
            email: The user's email address

        Returns:
            The newly created User object.

        Raises:
            ValidationError: If input validation fails.
        """
        # Validate inputs
        self._validate_username(username)
        self._validate_password(password)
        self._validate_email(email)

        username = username.strip()
        email = email.strip().lower()

        # Check if username already exists
        if username.lower() in {u.lower() for u in self._users}:
            raise ValidationError(f"Username '{username}' is already taken.")

        # Check if email already exists
        for user in self._users.values():
            if user.email == email:
                raise ValidationError(f"Email '{email}' is already registered.")

        # Hash password and create user
        password_hash, _ = self._hash_password(password)
        user = User(
            user_id=self._next_id,
            username=username,
            password_hash=password_hash,
            email=email,
        )
        self._users[username] = user
        self._next_id += 1
        return user

    def login(self, username: str, password: str) -> Dict:
        """
        Authenticate a user with username and password.

        Args:
            username: The user's username.
            password: The user's password.

        Returns:
            A dict containing login result with user info and a session token.

        Raises:
            ValidationError: If input is empty or invalid type.
            InvalidCredentialsError: If username or password is wrong.
            AccountDisabledError: If the account is disabled or locked.
        """
        # Basic input validation
        if not username or not isinstance(username, str):
            raise ValidationError("Username is required.")
        if not password or not isinstance(password, str):
            raise ValidationError("Password is required.")

        username = username.strip()

        # Check if account is locked due to too many failed attempts
        if self._failed_attempts.get(username, 0) >= self.MAX_FAILED_ATTEMPTS:
            raise AccountDisabledError(
                "Account is locked due to too many failed login attempts. "
                "Please contact support."
            )

        # Look up user
        user = self._users.get(username)
        if user is None:
            # Don't reveal whether username exists - increment attempts anyway
            self._failed_attempts[username] = self._failed_attempts.get(username, 0) + 1
            raise InvalidCredentialsError("Invalid username or password.")

        # Check if account is active
        if not user.is_active:
            raise AccountDisabledError("This account has been disabled.")

        # Verify password
        if not self._verify_password(password, user.password_hash):
            self._failed_attempts[username] = self._failed_attempts.get(username, 0) + 1
            remaining = self.MAX_FAILED_ATTEMPTS - self._failed_attempts[username]
            if remaining <= 0:
                raise AccountDisabledError(
                    "Account is locked due to too many failed login attempts."
                )
            raise InvalidCredentialsError("Invalid username or password.")

        # Successful login - reset failed attempts and update last login
        self._failed_attempts[username] = 0
        user.last_login = datetime.utcnow()

        # Generate session token
        session_token = secrets.token_urlsafe(32)

        return {
            "success": True,
            "message": "Login successful.",
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
            },
            "session_token": session_token,
        }

    def disable_user(self, username: str) -> None:
        """Disable a user account."""
        user = self._users.get(username)
        if user:
            user.is_active = False

    def enable_user(self, username: str) -> None:
        """Enable a user account."""
        user = self._users.get(username)
        if user:
            user.is_active = True

    def reset_failed_attempts(self, username: str) -> None:
        """Reset failed login attempts for a user (admin action)."""
        self._failed_attempts[username] = 0

    def get_user(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return self._users.get(username)