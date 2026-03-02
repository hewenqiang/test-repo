from flask import Flask, request, jsonify
from datetime import datetime, timezone
import uuid

from repositories.user_repository import UserRepository
from services.password_service import PasswordService
from validators.registration_validator import RegistrationValidator

app = Flask(__name__)

# In-memory storage for todos
todos = {}

# Shared user repository instance
user_repository = UserRepository()


def create_app():
    """Factory function to create and configure the Flask app."""
    return app


def generate_id():
    """Generate a unique ID for a todo item."""
    return str(uuid.uuid4())


def validate_todo_input(data, require_title=True):
    """
    Validate input data for creating/updating a todo.
    Returns a tuple of (validated_data, error_message).
    """
    if data is None:
        return None, "Request body must be valid JSON"

    errors = []

    if require_title:
        if "title" not in data:
            errors.append("'title' is required")
        elif not isinstance(data["title"], str) or not data["title"].strip():
            errors.append("'title' must be a non-empty string")

    if "title" in data and not require_title:
        if not isinstance(data["title"], str) or not data["title"].strip():
            errors.append("'title' must be a non-empty string")

    if "completed" in data:
        if not isinstance(data["completed"], bool):
            errors.append("'completed' must be a boolean")

    if errors:
        return None, "; ".join(errors)

    return data, None


@app.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    email = data.get("email", "")
    password = data.get("password", "")
    confirm_password = data.get("confirm_password")

    is_valid, errors = RegistrationValidator.validate_registration(email, password, confirm_password)
    if not is_valid:
        return jsonify({"error": errors}), 400

    if user_repository.exists_by_email(email):
        return jsonify({"error": "Email already registered."}), 409

    password_hash, salt = PasswordService.create_password_hash(password)
    from models.user import User
    user = User(email=email.strip(), password_hash=password_hash, salt=salt)
    user_repository.save(user)

    return jsonify({
        "message": "User registered successfully.",
        "user": {
            "id": user.id,
            "email": user.email,
        }
    }), 201


@app.route("/change-password", methods=["POST"])
def change_password():
    """
    Change a user's password.
    Requires: email, old_password, new_password, confirm_new_password
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    email = data.get("email", "")
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")
    confirm_new_password = data.get("confirm_new_password")

    # Validate email is provided
    if not email or not isinstance(email, str) or not email.strip():
        return jsonify({"error": "Email is required."}), 400

    # Validate old password is provided
    if not old_password or not isinstance(old_password, str):
        return jsonify({"error": "Old password is required."}), 400

    # Validate new password format
    is_valid, password_error = RegistrationValidator.validate_password(new_password)
    if not is_valid:
        return jsonify({"error": password_error}), 400

    # Validate confirm password matches
    if confirm_new_password is not None and new_password != confirm_new_password:
        return jsonify({"error": "New passwords do not match."}), 400

    # Check new password is different from old password
    if old_password == new_password:
        return jsonify({"error": "New password must be different from old password."}), 400

    # Find user by email
    user = user_repository.find_by_email(email.strip())
    if user is None:
        return jsonify({"error": "User not found."}), 404

    # Verify old password
    if not PasswordService.verify_password(old_password, user.password_hash, user.salt):
        return jsonify({"error": "Old password is incorrect."}), 401

    # Create new password hash and update user
    new_hash, new_salt = PasswordService.create_password_hash(new_password)
    user.password_hash = new_hash
    user.salt = new_salt
    user_repository.save(user)

    return jsonify({"message": "Password changed successfully."}), 200


@app.route("/todos", methods=["POST"])
def create_todo():
    """Create a new todo item."""
    data = request.get_json(silent=True)
    validated, error = validate_todo_input(data, require_title=True)

    if error:
        return jsonify({"error": error}), 400

    todo_id = generate_id()
    todo = {
        "id": todo_id,
        "title": validated["title"].strip(),
        "completed": validated.get("completed", False),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    todos[todo_id] = todo
    return jsonify(todo), 201


@app.route("/todos", methods=["GET"])
def list_todos():
    """
    List all todos with optional filtering.
    Query params:
      - completed: filter by completion status (true/false)
    """
    completed_filter = request.args.get("completed")

    result = list(todos.values())

    # Apply optional completed filter
    if completed_filter is not None:
        if completed_filter.lower() == "true":
            result = [t for t in result if t["completed"] is True]
        elif completed_filter.lower() == "false":
            result = [t for t in result if t["completed"] is False]
        else:
            return jsonify({"error": "'completed' filter must be 'true' or 'false'"}), 400

    # Sort by created_at descending (newest first)
    result.sort(key=lambda t: t["created_at"], reverse=True)

    return jsonify({"todos": result, "count": len(result)}), 200


@app.route("/todos/<todo_id>", methods=["GET"])
def get_todo(todo_id):
    """Retrieve a single todo by ID."""
    todo = todos.get(todo_id)
    if todo is None:
        return jsonify({"error": f"Todo with id '{todo_id}' not found"}), 404

    return jsonify(todo), 200


@app.route("/todos/<todo_id>", methods=["PUT"])
def update_todo(todo_id):
    """
    Update an existing todo item.
    Supports partial updates (only provided fields are updated).
    """
    todo = todos.get(todo_id)
    if todo is None:
        return jsonify({"error": f"Todo with id '{todo_id}' not found"}), 404

    data = request.get_json(silent=True)
    validated, error = validate_todo_input(data, require_title=False)

    if error:
        return jsonify({"error": error}), 400

    # Check that at least one updatable field is provided
    updatable_fields = {"title", "completed"}
    provided_fields = set(validated.keys()) & updatable_fields
    if not provided_fields:
        return jsonify({"error": "At least one of 'title' or 'completed' must be provided"}), 400

    # Apply updates
    if "title" in validated:
        todo["title"] = validated["title"].strip()
    if "completed" in validated:
        todo["completed"] = validated["completed"]

    return jsonify(todo), 200


@app.route("/todos/<todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    """Delete a todo by ID."""
    todo = todos.pop(todo_id, None)
    if todo is None:
        return jsonify({"error": f"Todo with id '{todo_id}' not found"}), 404

    return jsonify({"message": f"Todo '{todo_id}' deleted successfully"}), 200


@app.route("/todos", methods=["DELETE"])
def delete_all_todos():
    """Delete all todos."""
    count = len(todos)
    todos.clear()
    return jsonify({"message": f"Deleted {count} todo(s)"}), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405


if __name__ == "__main__":
    app.run(debug=True, port=5000)