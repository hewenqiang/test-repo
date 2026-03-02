import pytest
import json
from app import app, user_repository


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        # Clear user repository before each test
        user_repository._users.clear()
        user_repository._email_index.clear()
        yield client


@pytest.fixture
def registered_user(client):
    """Register a user and return the registration data."""
    response = client.post(
        "/register",
        data=json.dumps({
            "email": "test@example.com",
            "password": "oldPass1",
            "confirm_password": "oldPass1"
        }),
        content_type="application/json",
    )
    return json.loads(response.data)


class TestChangePassword:
    """Tests for POST /change-password endpoint."""

    def test_change_password_success(self, client, registered_user):
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "old_password": "oldPass1",
                "new_password": "newPass2",
                "confirm_new_password": "newPass2"
            }),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Password changed successfully."

    def test_change_password_can_login_with_new_password(self, client, registered_user):
        """After changing password, verify new password works."""
        client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "old_password": "oldPass1",
                "new_password": "newPass2",
                "confirm_new_password": "newPass2"
            }),
            content_type="application/json",
        )
        # Verify new password works by trying to change again
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "old_password": "newPass2",
                "new_password": "anotherPass3",
                "confirm_new_password": "anotherPass3"
            }),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_change_password_old_password_no_longer_works(self, client, registered_user):
        """After changing password, old password should not work."""
        client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "old_password": "oldPass1",
                "new_password": "newPass2",
                "confirm_new_password": "newPass2"
            }),
            content_type="application/json",
        )
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "old_password": "oldPass1",
                "new_password": "anotherPass3",
                "confirm_new_password": "anotherPass3"
            }),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_change_password_invalid_json(self, client, registered_user):
        response = client.post(
            "/change-password",
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Request body must be valid JSON" in data["error"]

    def test_change_password_missing_email(self, client, registered_user):
        response = client.post(
            "/change-password",
            data=json.dumps({
                "old_password": "oldPass1",
                "new_password": "newPass2",
                "confirm_new_password": "newPass2"
            }),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Email is required" in data["error"]

    def test_change_password_empty_email(self, client, registered_user):
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "",
                "old_password": "oldPass1",
                "new_password": "newPass2",
                "confirm_new_password": "newPass2"
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_change_password_missing_old_password(self, client, registered_user):
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "new_password": "newPass2",
                "confirm_new_password": "newPass2"
            }),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Old password is required" in data["error"]

    def test_change_password_wrong_old_password(self, client, registered_user):
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "old_password": "wrongPass1",
                "new_password": "newPass2",
                "confirm_new_password": "newPass2"
            }),
            content_type="application/json",
        )
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "Old password is incorrect" in data["error"]

    def test_change_password_user_not_found(self, client):
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "nonexistent@example.com",
                "old_password": "oldPass1",
                "new_password": "newPass2",
                "confirm_new_password": "newPass2"
            }),
            content_type="application/json",
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "User not found" in data["error"]

    def test_change_password_new_password_too_short(self, client, registered_user):
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "old_password": "oldPass1",
                "new_password": "ab1",
                "confirm_new_password": "ab1"
            }),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "at least 6 characters" in data["error"]

    def test_change_password_new_password_no_letter(self, client, registered_user):
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "old_password": "oldPass1",
                "new_password": "123456",
                "confirm_new_password": "123456"
            }),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "letter" in data["error"]

    def test_change_password_new_password_no_digit(self, client, registered_user):
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "old_password": "oldPass1",
                "new_password": "abcdef",
                "confirm_new_password": "abcdef"
            }),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "digit" in data["error"]

    def test_change_password_confirm_mismatch(self, client, registered_user):
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "old_password": "oldPass1",
                "new_password": "newPass2",
                "confirm_new_password": "differentPass3"
            }),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "do not match" in data["error"]

    def test_change_password_same_as_old(self, client, registered_user):
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "old_password": "oldPass1",
                "new_password": "oldPass1",
                "confirm_new_password": "oldPass1"
            }),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "different from old password" in data["error"]

    def test_change_password_without_confirm(self, client, registered_user):
        """Change password without confirm_new_password field should work."""
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "test@example.com",
                "old_password": "oldPass1",
                "new_password": "newPass2"
            }),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Password changed successfully."

    def test_change_password_case_insensitive_email(self, client, registered_user):
        """Email lookup should be case-insensitive."""
        response = client.post(
            "/change-password",
            data=json.dumps({
                "email": "TEST@EXAMPLE.COM",
                "old_password": "oldPass1",
                "new_password": "newPass2",
                "confirm_new_password": "newPass2"
            }),
            content_type="application/json",
        )
        assert response.status_code == 200


class TestRegister:
    """Tests for POST /register endpoint."""

    def test_register_success(self, client):
        response = client.post(
            "/register",
            data=json.dumps({
                "email": "user@example.com",
                "password": "myPass1",
                "confirm_password": "myPass1"
            }),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["message"] == "User registered successfully."
        assert data["user"]["email"] == "user@example.com"

    def test_register_duplicate_email(self, client):
        client.post(
            "/register",
            data=json.dumps({
                "email": "user@example.com",
                "password": "myPass1",
                "confirm_password": "myPass1"
            }),
            content_type="application/json",
        )
        response = client.post(
            "/register",
            data=json.dumps({
                "email": "user@example.com",
                "password": "myPass2",
                "confirm_password": "myPass2"
            }),
            content_type="application/json",
        )
        assert response.status_code == 409

    def test_register_invalid_email(self, client):
        response = client.post(
            "/register",
            data=json.dumps({
                "email": "not-an-email",
                "password": "myPass1",
                "confirm_password": "myPass1"
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_register_weak_password(self, client):
        response = client.post(
            "/register",
            data=json.dumps({
                "email": "user@example.com",
                "password": "123",
                "confirm_password": "123"
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_register_password_mismatch(self, client):
        response = client.post(
            "/register",
            data=json.dumps({
                "email": "user@example.com",
                "password": "myPass1",
                "confirm_password": "myPass2"
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_register_invalid_json(self, client):
        response = client.post(
            "/register",
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400