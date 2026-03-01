import re
import hashlib
import uuid
from datetime import datetime


class User:
    """Represents a registered user."""

    def __init__(self, email: str, password_hash: str, salt: str):
        self.id = str(uuid.uuid4())
        self.email = email
        self.password_hash = password_hash
        self.salt = salt
        self.created_at = datetime.utcnow()
        self.is_active = True

    def __repr__(self):
        return f"User(id={self.id}, email={self.email}, created_at={self.created_at})"