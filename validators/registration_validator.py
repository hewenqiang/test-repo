import re


class RegistrationValidator:
    """Validates user registration input (email and password)."""

    # Standard email regex pattern
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    # Password must contain at least one letter and one digit, minimum 6 characters
    PASSWORD_MIN_LENGTH = 6
    PASSWORD_LETTER_PATTERN = re.compile(r'[a-zA-Z]')
    PASSWORD_DIGIT_PATTERN = re.compile(r'[0-9]')

    @classmethod
    def validate_email(cls, email: str) -> tuple[bool, str]:
        """
        Validate email format.

        Returns:
            tuple of (is_valid, error_message)
        """
        if not email or not isinstance(email, str):
            return False, "Email is required."

        email = email.strip()

        if not email:
            return False, "Email is required."

        if not cls.EMAIL_PATTERN.match(email):
            return False, "Invalid email format."

        return True, ""

    @classmethod
    def validate_password(cls, password: str) -> tuple[bool, str]:
        """
        Validate password:
        - Must be at least 6 characters long
        - Must contain at least one English letter (a-z or A-Z)
        - Must contain at least one digit (0-9)

        Returns:
            tuple of (is_valid, error_message)
        """
        if not password or not isinstance(password, str):
            return False, "Password is required."

        if len(password) < cls.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {cls.PASSWORD_MIN_LENGTH} characters long."

        if not cls.PASSWORD_LETTER_PATTERN.search(password):
            return False, "Password must contain at least one English letter."

        if not cls.PASSWORD_DIGIT_PATTERN.search(password):
            return False, "Password must contain at least one digit."

        return True, ""

    @classmethod
    def validate_registration(cls, email: str, password: str, confirm_password: str = None) -> tuple[bool, list[str]]:
        """
        Validate all registration fields.

        Returns:
            tuple of (is_valid, list_of_error_messages)
        """
        errors = []

        email_valid, email_error = cls.validate_email(email)
        if not email_valid:
            errors.append(email_error)

        password_valid, password_error = cls.validate_password(password)
        if not password_valid:
            errors.append(password_error)

        # If confirm_password is provided, check it matches
        if confirm_password is not None and password != confirm_password:
            errors.append("Passwords do not match.")

        is_valid = len(errors) == 0
        return is_valid, errors