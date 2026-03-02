import pytest
import json
from app import app, todos


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        # Clear todos before each test
        todos.clear()
        yield client


@pytest.fixture
def sample_todo(client):
    """Create and return a sample todo for tests that need existing data."""
    response = client.post(
        "/todos",
        data=json.dumps({"title": "Sample Todo"}),
        content_type="application/json",
    )
    return json.loads(response.data)


class TestCreateTodo:
    """Tests for POST /todos endpoint."""

    def test_create_todo_success(self, client):
        response = client.post(
            "/todos",
            data=json.dumps({"title": "Buy groceries"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["title"] == "Buy groceries"
        assert data["completed"] is False
        assert "id" in data
        assert "created_at" in data

    def test_create_todo_with_completed_true(self, client):
        response = client.post(
            "/todos",
            data=json.dumps({"title": "Already done", "completed": True}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["completed"] is True

    def test_create_todo_with_completed_false(self, client):
        response = client.post(
            "/todos",
            data=json.dumps({"title": "Not done", "completed": False}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["completed"] is False

    def test_create_todo_missing_title(self, client):
        response = client.post(
            "/todos",
            data=json.dumps({"completed": True}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "'title' is required" in data["error"]

    def test_create_todo_empty_title(self, client):
        response = client.post(
            "/todos",
            data=json.dumps({"title": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_create_todo_whitespace_title(self, client):
        response = client.post(
            "/todos",
            data=json.dumps({"title": "   "}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_todo_title_not_string(self, client):
        response = client.post(
            "/todos",
            data=json.dumps({"title": 123}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_todo_completed_not_boolean(self, client):
        response = client.post(
            "/todos",
            data=json.dumps({"title": "Test", "completed": "yes"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "'completed' must be a boolean" in data["error"]

    def test_create_todo_invalid_json(self, client):
        response = client.post(
            "/todos",
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_todo_strips_whitespace_from_title(self, client):
        response = client.post(
            "/todos",
            data=json.dumps({"title": "  Buy milk  "}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["title"] == "Buy milk"

    def test_create_todo_stored_in_memory(self, client):
        assert len(todos) == 0
        client.post(
            "/todos",
            data=json.dumps({"title": "Test"}),
            content_type="application/json",
        )
        assert len(todos) == 1


class TestListTodos:
    """Tests for GET /todos endpoint."""

    def test_list_todos_empty(self, client):
        response = client.get("/todos")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["todos"] == []
        assert data["count"] == 0

    def test_list_todos_with_items(self, client, sample_todo):
        # Create another todo
        client.post(
            "/todos",
            data=json.dumps({"title": "Second todo"}),
            content_type="application/json",
        )
        response = client.get("/todos")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["count"] == 2
        assert len(data["todos"]) == 2

    def test_list_todos_filter_completed_true(self, client):
        client.post(
            "/todos",
            data=json.dumps({"title": "Done", "completed": True}),
            content_type="application/json",
        )
        client.post(
            "/todos",
            data=json.dumps({"title": "Not done", "completed": False}),
            content_type="application/json",
        )
        response = client.get("/todos?completed=true")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["count"] == 1
        assert data["todos"][0]["title"] == "Done"

    def test_list_todos_filter_completed_false(self, client):
        client.post(
            "/todos",
            data=json.dumps({"title": "Done", "completed": True}),
            content_type="application/json",
        )
        client.post(
            "/todos",
            data=json.dumps({"title": "Not done", "completed": False}),
            content_type="application/json",
        )
        response = client.get("/todos?completed=false")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["count"] == 1
        assert data["todos"][0]["title"] == "Not done"

    def test_list_todos_filter_invalid_value(self, client):
        response = client.get("/todos?completed=maybe")
        assert response.status_code == 400

    def test_list_todos_sorted_newest_first(self, client):
        import time

        client.post(
            "/todos",
            data=json.dumps({"title": "First"}),
            content_type="application/json",
        )
        time.sleep(0.01)  # Small delay to ensure different timestamps
        client.post(
            "/todos",
            data=json.dumps({"title": "Second"}),
            content_type="application/json",
        )
        response = client.get("/todos")
        data = json.loads(response.data)
        assert data["todos"][0]["title"] == "Second"
        assert data["todos"][1]["title"] == "First"


class TestGetTodo:
    """Tests for GET /todos/<id> endpoint."""

    def test_get_todo_success(self, client, sample_todo):
        todo_id = sample_todo["id"]
        response = client.get(f"/todos/{todo_id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == todo_id
        assert data["title"] == "Sample Todo"

    def test_get_todo_not_found(self, client):
        response = client.get("/todos/nonexistent-id")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert "not found" in data["error"]


class TestUpdateTodo:
    """Tests for PUT /todos/<id> endpoint."""

    def test_update_todo_title(self, client, sample_todo):
        todo_id = sample_todo["id"]
        response = client.put(
            f"/todos/{todo_id}",
            data=json.dumps({"title": "Updated Title"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["title"] == "Updated Title"
        assert data["completed"] is False  # unchanged

    def test_update_todo_completed(self, client, sample_todo):
        todo_id = sample_todo["id"]
        response = client.put(
            f"/todos/{todo_id}",
            data=json.dumps({"completed": True}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["completed"] is True
        assert data["title"] == "Sample Todo"  # unchanged

    def test_update_todo_both_fields(self, client, sample_todo):
        todo_id = sample_todo["id"]
        response = client.put(
            f"/todos/{todo_id}",
            data=json.dumps({"title": "New Title", "completed": True}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["title"] == "New Title"
        assert data["completed"] is True

    def test_update_todo_not_found(self, client):
        response = client.put(
            "/todos/nonexistent-id",
            data=json.dumps({"title": "Updated"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_todo_no_updatable_fields(self, client, sample_todo):
        todo_id = sample_todo["id"]
        response = client.put(
            f"/todos/{todo_id}",
            data=json.dumps({"extra_field": "value"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_update_todo_invalid_json(self, client, sample_todo):
        todo_id = sample_todo["id"]
        response = client.put(
            f"/todos/{todo_id}",
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_update_todo_empty_title(self, client, sample_todo):
        todo_id = sample_todo["id"]
        response = client.put(
            f"/todos/{todo_id}",
            data=json.dumps({"title": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_update_todo_invalid_completed(self, client, sample_todo):
        todo_id = sample_todo["id"]
        response = client.put(
            f"/todos/{todo_id}",
            data=json.dumps({"completed": "yes"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_update_todo_strips_title_whitespace(self, client, sample_todo):
        todo_id = sample_todo["id"]
        response = client.put(
            f"/todos/{todo_id}",
            data=json.dumps({"title": "  Trimmed  "}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["title"] == "Trimmed"


class TestDeleteTodo:
    """Tests for DELETE /todos/<id> endpoint."""

    def test_delete_todo_success(self, client, sample_todo):
        todo_id = sample_todo["id"]
        response = client.delete(f"/todos/{todo_id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "deleted successfully" in data["message"]

        # Verify it's actually gone
        get_response = client.get(f"/todos/{todo_id}")
        assert get_response.status_code == 404

    def test_delete_todo_not_found(self, client):
        response = client.delete("/todos/nonexistent-id")
        assert response.status_code == 404

    def test_delete_todo_removes_from_storage(self, client, sample_todo):
        todo_id = sample_todo["id"]
        assert todo_id in todos
        client.delete(f"/todos/{todo_id}")
        assert todo_id not in todos


class TestDeleteAllTodos:
    """Tests for DELETE /todos endpoint."""

    def test_delete_all_todos_empty(self, client):
        response = client.delete("/todos")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "Deleted 0 todo(s)" in data["message"]

    def test_delete_all_todos_with_items(self, client):
        # Create multiple todos
        client.post(
            "/todos",
            data=json.dumps({"title": "Todo 1"}),
            content_type="application/json",
        )
        client.post(
            "/todos",
            data=json.dumps({"title": "Todo 2"}),
            content_type="application/json",
        )
        response = client.delete("/todos")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "Deleted 2 todo(s)" in data["message"]
        assert len(todos) == 0


class TestErrorHandlers:
    """Tests for error handlers."""

    def test_404_unknown_route(self, client):
        response = client.get("/unknown")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

    def test_405_method_not_allowed(self, client):
        response = client.patch("/todos")
        assert response.status_code == 405
        data = json.loads(response.data)
        assert "error" in data


class TestValidation:
    """Tests for the validate_todo_input function."""

    def test_create_multiple_errors(self, client):
        """Test that multiple validation errors are reported."""
        response = client.post(
            "/todos",
            data=json.dumps({"completed": "not_bool"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        # Should contain both title required and completed type errors
        assert "'title' is required" in data["error"]
        assert "'completed' must be a boolean" in data["error"]


class TestIntegration:
    """Integration tests for full CRUD workflow."""

    def test_full_crud_lifecycle(self, client):
        # Create
        create_resp = client.post(
            "/todos",
            data=json.dumps({"title": "Integration Test Todo"}),
            content_type="application/json",
        )
        assert create_resp.status_code == 201
        todo = json.loads(create_resp.data)
        todo_id = todo["id"]

        # Read
        get_resp = client.get(f"/todos/{todo_id}")
        assert get_resp.status_code == 200
        assert json.loads(get_resp.data)["title"] == "Integration Test Todo"

        # Update
        update_resp = client.put(
            f"/todos/{todo_id}",
            data=json.dumps({"title": "Updated Todo", "completed": True}),
            content_type="application/json",
        )
        assert update_resp.status_code == 200
        updated = json.loads(update_resp.data)
        assert updated["title"] == "Updated Todo"
        assert updated["completed"] is True

        # List
        list_resp = client.get("/todos")
        assert json.loads(list_resp.data)["count"] == 1

        # Delete
        delete_resp = client.delete(f"/todos/{todo_id}")
        assert delete_resp.status_code == 200

        # Verify deleted
        verify_resp = client.get(f"/todos/{todo_id}")
        assert verify_resp.status_code == 404

    def test_create_multiple_and_filter(self, client):
        """Test creating multiple todos and filtering them."""
        titles = ["Task A", "Task B", "Task C"]
        for i, title in enumerate(titles):
            client.post(
                "/todos",
                data=json.dumps({"title": title, "completed": i % 2 == 0}),
                content_type="application/json",
            )

        # All todos
        all_resp = client.get("/todos")
        assert json.loads(all_resp.data)["count"] == 3

        # Completed only (Task A and Task C)
        completed_resp = client.get("/todos?completed=true")
        assert json.loads(completed_resp.data)["count"] == 2

        # Not completed only (Task B)
        incomplete_resp = client.get("/todos?completed=false")
        assert json.loads(incomplete_resp.data)["count"] == 1