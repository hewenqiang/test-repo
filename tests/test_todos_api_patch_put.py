import json
import pytest
from app import app, todos


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        todos.clear()
        yield client


def create_todo(client, **fields):
    resp = client.post(
        "/todos",
        data=json.dumps({"title": fields.get("title", "Title"), **{k: v for k, v in fields.items() if k != "title"}}),
        content_type="application/json",
    )
    assert resp.status_code == 201
    return json.loads(resp.data)


class TestPatch:
    def test_patch_title_only(self, client):
        todo = create_todo(client, title="Alpha", completed=False)
        tid = todo["id"]
        resp = client.patch(
            f"/todos/{tid}",
            data=json.dumps({"title": "Beta"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["title"] == "Beta"
        assert data["completed"] is False

    def test_patch_completed_only(self, client):
        todo = create_todo(client, title="Alpha", completed=False)
        tid = todo["id"]
        resp = client.patch(
            f"/todos/{tid}",
            data=json.dumps({"completed": True}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["title"] == "Alpha"
        assert data["completed"] is True

    def test_patch_not_found(self, client):
        resp = client.patch(
            "/todos/nonexistent",
            data=json.dumps({"title": "X"}),
            content_type="application/json",
        )
        assert resp.status_code == 404


class TestPut:
    def test_put_requires_both_fields_title_only(self, client):
        todo = create_todo(client, title="Alpha", completed=False)
        tid = todo["id"]
        resp = client.put(
            f"/todos/{tid}",
            data=json.dumps({"title": "Only Title"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "Both 'title' and 'completed' are required" in data["error"]

    def test_put_requires_both_fields_completed_only(self, client):
        todo = create_todo(client, title="Alpha", completed=False)
        tid = todo["id"]
        resp = client.put(
            f"/todos/{tid}",
            data=json.dumps({"completed": True}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "Both 'title' and 'completed' are required" in data["error"]

    def test_put_full_replacement_success(self, client):
        todo = create_todo(client, title="Alpha", completed=False)
        tid = todo["id"]
        resp = client.put(
            f"/todos/{tid}",
            data=json.dumps({"title": "Gamma", "completed": True}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["title"] == "Gamma"
        assert data["completed"] is True

    def test_put_not_found(self, client):
        resp = client.put(
            "/todos/nonexistent",
            data=json.dumps({"title": "Z", "completed": False}),
            content_type="application/json",
        )
        assert resp.status_code == 404
