import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import Todo


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create test client with database override."""
    def get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[SessionLocal] = get_test_db
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestRootEndpoint:
    @pytest.mark.asyncio
    async def test_read_root(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Todo API is running!"


class TestTodoCRUD:
    @pytest.mark.asyncio
    async def test_create_todo(self, client):
        response = await client.post("/todos", json={
            "title": "Test Todo",
            "description": "Test Description"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Todo"
        assert data["description"] == "Test Description"
        assert data["completed"] is False
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_todo_without_title(self, client):
        response = await client.post("/todos", json={
            "description": "No title"
        })
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_todo_empty_title(self, client):
        response = await client.post("/todos", json={
            "title": "  ",
            "description": "Empty title"
        })
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_read_all_todos(self, client):
        # Create a todo first
        await client.post("/todos", json={
            "title": "First Todo",
            "description": "First"
        })
        await client.post("/todos", json={
            "title": "Second Todo",
            "description": "Second"
        })
        response = await client.get("/todos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_read_todo_by_id(self, client):
        # Create a todo first
        create_response = await client.post("/todos", json={
            "title": "Get Me",
            "description": "Get this"
        })
        todo_id = create_response.json()["id"]
        response = await client.get(f"/todos/{todo_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Get Me"

    @pytest.mark.asyncio
    async def test_read_todo_not_found(self, client):
        response = await client.get("/todos/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_todo(self, client):
        # Create a todo first
        create_response = await client.post("/todos", json={
            "title": "Update Me",
            "description": "Before update"
        })
        todo_id = create_response.json()["id"]
        response = await client.put(f"/todos/{todo_id}", json={
            "title": "Updated Todo",
            "completed": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Todo"
        assert data["completed"] is True

    @pytest.mark.asyncio
    async def test_update_todo_not_found(self, client):
        response = await client.put("/todos/99999", json={
            "title": "Should Fail"
        })
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_todo(self, client):
        # Create a todo first
        create_response = await client.post("/todos", json={
            "title": "Delete Me"
        })
        todo_id = create_response.json()["id"]
        response = await client.delete(f"/todos/{todo_id}")
        assert response.status_code == 204
        # Verify it's deleted
        get_response = await client.get(f"/todos/{todo_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_todo_not_found(self, client):
        response = await client.delete("/todos/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_filter_by_completed(self, client):
        # Create todos with different completed status
        await client.post("/todos", json={"title": "Todo 1", "description": "Pending"})
        await client.post("/todos", json={"title": "Todo 2", "description": "Done", "completed": True})
        
        # Get only completed
        response = await client.get("/todos?completed=true")
        assert response.status_code == 200
        data = response.json()
        assert all(t["completed"] is True for t in data)
        
        # Get only pending
        response = await client.get("/todos?completed=false")
        assert response.status_code == 200
        data = response.json()
        assert all(t["completed"] is False for t in data)

    @pytest.mark.asyncio
    async def test_pagination(self, client):
        # Create multiple todos
        for i in range(5):
            await client.post("/todos", json={"title": f"Todo {i}"})
        
        # Get with limit
        response = await client.get("/todos?limit=3")
        assert response.status_code == 200
        assert len(response.json()) <= 3

    @pytest.mark.asyncio
    async def test_todo_stats(self, client):
        # Create some todos
        await client.post("/todos", json={"title": "Todo 1"})
        await client.post("/todos", json={"title": "Todo 2"})
        await client.post("/todos", json={"title": "Todo 3"})
        
        response = await client.get("/todos/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "completed" in data
        assert "pending" in data
        assert data["total"] >= 3


class TestTodosEndpoint:
    @pytest.mark.asyncio
    async def test_get_todos_endpoint(self, client):
        response = await client.get("/todos")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_put_todos_endpoint(self, client):
        # Create a todo first
        create_response = await client.post("/todos", json={"title": "Test"})
        todo_id = create_response.json()["id"]
        
        response = await client.put(f"/todos/{todo_id}", json={
            "title": "Updated",
            "completed": True
        })
        assert response.status_code == 200
        assert response.json()["completed"] is True

    @pytest.mark.asyncio
    async def test_delete_todos_endpoint(self, client):
        # Create a todo first
        create_response = await client.post("/todos", json={"title": "Test"})
        todo_id = create_response.json()["id"]
        
        response = await client.delete(f"/todos/{todo_id}")
        assert response.status_code == 204


@pytest.fixture
def test_client():
    """Synchronous test client."""
    from app.main import app
    from fastapi.testclient import TestClient
    Base.metadata.create_all(bind=engine)
    return TestClient(app)


class TestSyncEndpoints:
    def test_create_todo_sync(self, test_client):
        response = test_client.post("/todos", json={
            "title": "Sync Test Todo",
            "description": "Sync Description"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Sync Test Todo"

    def test_read_todo_sync(self, test_client):
        response = test_client.post("/todos", json={"title": "Sync Read"})
        todo_id = response.json()["id"]
        get_response = test_client.get(f"/todos/{todo_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Sync Read"

    def test_update_todo_sync(self, test_client):
        response = test_client.post("/todos", json={"title": "Sync Update"})
        todo_id = response.json()["id"]
        update_response = test_client.put(f"/todos/{todo_id}", json={
            "title": "Updated Sync"
        })
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated Sync"

    def test_delete_todo_sync(self, test_client):
        response = test_client.post("/todos", json={"title": "Sync Delete"})
        todo_id = response.json()["id"]
        delete_response = test_client.delete(f"/todos/{todo_id}")
        assert delete_response.status_code == 204
