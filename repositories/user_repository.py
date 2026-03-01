from models.user import User
from typing import Optional


class UserRepository:
    """
    In-memory user repository.
    In production, this would be backed by a database.
    """

    def __init__(self):
        self._users: dict[str, User] = {}  # keyed by user id
        self._email_index: dict[str, str] = {}  # email -> user_id mapping

    def save(self, user: User) -> User:
        """Save a user to the repository."""
        self._users[user.id] = user
        self._email_index[user.email.lower()] = user.id
        return user

    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address (case-insensitive)."""
        user_id = self._email_index.get(email.lower())
        if user_id:
            return self._users.get(user_id)
        return None

    def find_by_id(self, user_id: str) -> Optional[User]:
        """Find a user by ID."""
        return self._users.get(user_id)

    def exists_by_email(self, email: str) -> bool:
        """Check if a user with the given email already exists."""
        return email.lower() in self._email_index

    def count(self) -> int:
        """Return the total number of users."""
        return len(self._users)

    def delete(self, user_id: str) -> bool:
        """Delete a user by ID."""
        user = self._users.get(user_id)
        if user:
            del self._email_index[user.email.lower()]
            del self._users[user_id]
            return True
        return False