from sqlalchemy.orm import Session
from app.models import Todo
from app.schemas import TodoCreate, TodoUpdate
from typing import List


def get_todos(db: Session, skip: int = 0, limit: int = 100, completed: bool = None) -> List[Todo]:
    query = db.query(Todo)
    if completed is not None:
        query = query.filter(Todo.completed == completed)
    return query.order_by(Todo.created_at.desc()).offset(skip).limit(limit).all()


def get_todo(db: Session, todo_id: int) -> Todo:
    return db.query(Todo).filter(Todo.id == todo_id).first()


def create_todo(db: Session, todo: TodoCreate) -> Todo:
    db_todo = Todo(title=todo.title, description=todo.description)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


def update_todo(db: Session, todo_id: int, todo: TodoUpdate) -> Todo:
    db_todo = get_todo(db, todo_id)
    if not db_todo:
        return None
    update_data = todo.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_todo, key, value)
    db.commit()
    db.refresh(db_todo)
    return db_todo


def delete_todo(db: Session, todo_id: int) -> bool:
    db_todo = get_todo(db, todo_id)
    if not db_todo:
        return False
    db.delete(db_todo)
    db.commit()
    return True
