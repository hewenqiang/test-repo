import hashlib
import os


class PasswordService:
    """Handles password hashing and verification using SHA-256 with salt."""

    @staticmethod
    def generate_salt() -> str:
        """Generate a random salt."""
        return os.urandom(32).hex()

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """
        Hash a password with the given salt using SHA-256.

        Args:
            password: Plain text password
            salt: Random salt string

        Returns:
            Hex digest of the hashed password
        """
        salted_password = f"{salt}{password}".encode('utf-8')
        return hashlib.sha256(salted_password).hexdigest()

    @classmethod
    def create_password_hash(cls, password: str) -> tuple[str, str]:
        """
        Create a password hash with a new salt.

        Returns:
            tuple of (password_hash, salt)
        """
        salt = cls.generate_salt()
        password_hash = cls.hash_password(password, salt)
        return password_hash, salt

    @classmethod
    def verify_password(cls, password: str, password_hash: str, salt: str) -> bool:
        """
        Verify a password against a stored hash and salt.

        Returns:
            True if the password matches, False otherwise
        """
        computed_hash = cls.hash_password(password, salt)
        return computed_hash == password_hash