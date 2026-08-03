import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import pytest
from fastapi.testclient import TestClient
from main import app
from database import init_db, get_db
import sqlite3

init_db()
client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    """Xoá sạch todos trước mỗi test"""
    with get_db() as conn:
        conn.execute("DELETE FROM todos")
    yield
    with get_db() as conn:
        conn.execute("DELETE FROM todos")

# ============ GET ALL TODOS ============
def test_get_empty_todos():
    res = client.get("/api/todos")
    assert res.status_code == 200
    assert res.json() == []

def test_get_todos_after_creation():
    client.post("/api/todos", json={"title": "Test 1"})
    client.post("/api/todos", json={"title": "Test 2"})
    res = client.get("/api/todos")
    assert res.status_code == 200
    assert len(res.json()) == 2

# ============ CREATE TODO ============
def test_create_todo():
    res = client.post("/api/todos", json={"title": "Buy milk", "description": "2 liters"})
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Buy milk"
    assert data["description"] == "2 liters"
    assert "id" in data

def test_create_todo_minimal():
    res = client.post("/api/todos", json={"title": "Just title"})
    assert res.status_code == 201
    assert res.json()["title"] == "Just title"

def test_create_todo_empty_title_fails():
    res = client.post("/api/todos", json={"title": ""})
    assert res.status_code == 422

def test_create_todo_missing_title():
    res = client.post("/api/todos", json={"description": "no title"})
    assert res.status_code == 422

# ============ GET SINGLE TODO ============
def test_get_single_todo():
    create = client.post("/api/todos", json={"title": "Find me"})
    todo_id = create.json()["id"]
    res = client.get(f"/api/todos/{todo_id}")
    assert res.status_code == 200
    assert res.json()["title"] == "Find me"

def test_get_todo_not_found():
    res = client.get("/api/todos/99999")
    assert res.status_code == 404

# ============ UPDATE TODO ============
def test_update_todo_title():
    create = client.post("/api/todos", json={"title": "Old title"})
    todo_id = create.json()["id"]
    res = client.put(f"/api/todos/{todo_id}", json={"title": "New title"})
    assert res.status_code == 200
    assert res.json()["title"] == "New title"

def test_update_todo_completed():
    create = client.post("/api/todos", json={"title": "Do something"})
    todo_id = create.json()["id"]
    res = client.put(f"/api/todos/{todo_id}", json={"completed": True})
    assert res.status_code == 200
    assert res.json()["completed"] is True

    # Verify in GET
    get_res = client.get(f"/api/todos/{todo_id}")
    assert get_res.json()["completed"] is True

def test_update_todo_not_found():
    res = client.put("/api/todos/99999", json={"title": "ghost"})
    assert res.status_code == 404

def test_update_todo_empty_body():
    create = client.post("/api/todos", json={"title": "test"})
    todo_id = create.json()["id"]
    res = client.put(f"/api/todos/{todo_id}", json={})
    assert res.status_code == 400

# ============ DELETE TODO ============
def test_delete_todo():
    create = client.post("/api/todos", json={"title": "Delete me"})
    todo_id = create.json()["id"]
    res = client.delete(f"/api/todos/{todo_id}")
    assert res.status_code == 204

    # Verify it's gone
    get_res = client.get(f"/api/todos/{todo_id}")
    assert get_res.status_code == 404

def test_delete_todo_not_found():
    res = client.delete("/api/todos/99999")
    assert res.status_code == 404

# ============ FULL CRUD WORKFLOW ============
def test_full_crud_workflow():
    # Create
    res = client.post("/api/todos", json={"title": "Full test", "description": "End to end"})
    assert res.status_code == 201
    todo_id = res.json()["id"]

    # Read
    res = client.get(f"/api/todos/{todo_id}")
    assert res.json()["title"] == "Full test"
    assert res.json()["completed"] is False

    # Update
    res = client.put(f"/api/todos/{todo_id}", json={"completed": True, "title": "Done!"})
    assert res.status_code == 200
    assert res.json()["completed"] is True

    # Verify in list
    res = client.get("/api/todos")
    found = [t for t in res.json() if t["id"] == todo_id]
    assert len(found) == 1
    assert found[0]["title"] == "Done!"

    # Delete
    res = client.delete(f"/api/todos/{todo_id}")
    assert res.status_code == 204

    # Verify gone
    res = client.get("/api/todos")
    assert all(t["id"] != todo_id for t in res.json())

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
