from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from database import get_db, init_db
from datetime import datetime

app = FastAPI(title="Todo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = ""

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

def row_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/api/todos", response_model=list[dict])
def get_todos():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM todos ORDER BY created_at DESC").fetchall()
    return [row_to_dict(r) for r in rows]

@app.get("/api/todos/{todo_id}", response_model=dict)
def get_todo(todo_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Todo not found")
    return row_to_dict(row)

@app.post("/api/todos", status_code=201)
def create_todo(todo: TodoCreate):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO todos (title, description) VALUES (?, ?)",
            (todo.title, todo.description)
        )
    return {"id": cursor.lastrowid, **todo.model_dump()}

@app.put("/api/todos/{todo_id}")
def update_todo(todo_id: int, todo: TodoUpdate):
    data = todo.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No data to update")
    with get_db() as conn:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Todo not found")
        fields = []
        values = []
        for key in data:
            if key == "completed":
                fields.append(f"{key} = ?")
                values.append(1 if data[key] else 0)
            else:
                fields.append(f"{key} = ?")
                values.append(data[key])
        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(todo_id)
        conn.execute(f"UPDATE todos SET {', '.join(fields)} WHERE id = ?", values)
    return {"id": todo_id, **data}

@app.delete("/api/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Todo not found")
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
