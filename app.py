from flask import Flask, request, jsonify
from datetime import datetime, timezone
import uuid

app = Flask(__name__)

# In-memory storage for todos
todos = {}


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