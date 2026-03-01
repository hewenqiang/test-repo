from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User model representing a registered user."""
    user_id: int
    username: str
    password_hash: str
    email: str
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

    def __repr__(self):
        return f"User(user_id={self.user_id}, username='{self.username}', email='{self.email}')"