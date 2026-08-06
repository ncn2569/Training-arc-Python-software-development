from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import engine, get_db
from app.models import Base, Todo
from app.schemas import TodoCreate, TodoUpdate, TodoResponse
from app.crud import get_todos, get_todo, create_todo, update_todo, delete_todo

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Todo API",
    description="A simple Todo API with FastAPI",
    version="1.0.0"
)


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Todo API is running!"}


@app.get("/todos", response_model=List[TodoResponse], tags=["Todos"])
def read_todos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    completed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Get all todos with optional filtering by completed status.
    """
    return get_todos(db, skip=skip, limit=limit, completed=completed)


@app.get("/todos/stats", tags=["Todos"])
def get_todo_stats(db: Session = Depends(get_db)):
    """
    Get statistics about todos.
    """
    all_todos = get_todos(db, skip=0, limit=1000)
    total = len(all_todos)
    completed = sum(1 for t in all_todos if t.completed)
    pending = total - completed
    return {
        "total": total,
        "completed": completed,
        "pending": pending
    }


@app.get("/todos/{todo_id}", response_model=TodoResponse, tags=["Todos"])
def read_todo(todo_id: int, db: Session = Depends(get_db)):
    """
    Get a specific todo by ID.
    """
    db_todo = get_todo(db, todo_id)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo


@app.post("/todos", response_model=TodoResponse, status_code=201, tags=["Todos"])
def create_todo_endpoint(todo: TodoCreate, db: Session = Depends(get_db)):
    """
    Create a new todo.
    """
    if not todo.title or not todo.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    return create_todo(db, todo)


@app.put("/todos/{todo_id}", response_model=TodoResponse, tags=["Todos"])
def update_todo_endpoint(todo_id: int, todo: TodoUpdate, db: Session = Depends(get_db)):
    """
    Update an existing todo.
    """
    db_todo = update_todo(db, todo_id, todo)
    if db_todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo


@app.delete("/todos/{todo_id}", status_code=204, tags=["Todos"])
def delete_todo_endpoint(todo_id: int, db: Session = Depends(get_db)):
    """
    Delete a todo by ID.
    """
    success = delete_todo(db, todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return None
