import pytest
from sqlalchemy.orm import Session
from app.models import Todo
from app.crud import (
    get_todos,
    get_todo,
    create_todo,
    update_todo,
    delete_todo
)
from app.schemas import TodoCreate, TodoUpdate


@pytest.fixture
def sample_todo():
    """Create a sample todo data."""
    return TodoCreate(title="Sample Todo", description="Sample Description")


class TestGetTodos:
    def test_get_all_todos(self, db_session):
        db_session.add(Todo(title="Todo 1"))
        db_session.add(Todo(title="Todo 2"))
        db_session.commit()
        
        todos = get_todos(db_session)
        assert len(todos) >= 2

    def test_get_todos_with_completed_filter(self, db_session):
        db_session.add(Todo(title="Pending Todo", completed=False))
        db_session.add(Todo(title="Done Todo", completed=True))
        db_session.commit()
        
        completed_todos = get_todos(db_session, completed=True)
        assert len(completed_todos) >= 1
        assert all(t.completed for t in completed_todos)
        
        pending_todos = get_todos(db_session, completed=False)
        assert len(pending_todos) >= 1
        assert all(not t.completed for t in pending_todos)


class TestGetTodo:
    def test_get_existing_todo(self, db_session):
        todo = db_session.add(Todo(title="Get Me"))
        db_session.commit()
        
        result = get_todo(db_session, 1)
        assert result is not None
        assert result.title == "Get Me"

    def test_get_non_existent_todo(self, db_session):
        result = get_todo(db_session, 99999)
        assert result is None


class TestCreateTodo:
    def test_create_todo(self, db_session, sample_todo):
        result = create_todo(db_session, sample_todo)
        assert result.id is not None
        assert result.title == "Sample Todo"
        assert result.description == "Sample Description"
        assert result.completed is False

    def test_create_todo_without_description(self, db_session):
        todo_create = TodoCreate(title="No Description")
        result = create_todo(db_session, todo_create)
        assert result is not None
        assert result.title == "No Description"
        assert result.description is None


class TestUpdateTodo:
    def test_update_todo(self, db_session):
        db_session.add(Todo(title="Update Me"))
        db_session.commit()
        
        update_data = TodoUpdate(title="Updated", completed=True)
        result = update_todo(db_session, 1, update_data)
        
        assert result.title == "Updated"
        assert result.completed is True

    def test_update_todo_partial(self, db_session):
        db_session.add(Todo(title="Partial Update", completed=False))
        db_session.commit()
        
        update_data = TodoUpdate(completed=True)
        result = update_todo(db_session, 1, update_data)
        
        assert result.title == "Partial Update"
        assert result.completed is True

    def test_update_non_existent_todo(self, db_session):
        result = update_todo(db_session, 99999, TodoUpdate(title="Should Fail"))
        assert result is None


class TestDeleteTodo:
    def test_delete_existing_todo(self, db_session):
        db_session.add(Todo(title="Delete Me"))
        db_session.commit()
        
        result = delete_todo(db_session, 1)
        assert result is True
        
        # Verify deletion
        todo = get_todo(db_session, 1)
        assert todo is None

    def test_delete_non_existent_todo(self, db_session):
        result = delete_todo(db_session, 99999)
        assert result is False
