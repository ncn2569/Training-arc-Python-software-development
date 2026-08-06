import React from 'react';
import TodoItem from './TodoItem';

const TodoList = ({ todos, onToggleTodo, onDeleteTodo, onUpdateTodo }) => {
  if (todos.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📋</div>
        <h3>No todos yet!</h3>
        <p>Add your first todo above to get started</p>
      </div>
    );
  }

  return (
    <div className="todo-list">
      {todos.map((todo) => (
        <TodoItem
          key={todo.id}
          todo={todo}
          onToggle={onToggleTodo}
          onDelete={onDeleteTodo}
          onUpdate={onUpdateTodo}
        />
      ))}
    </div>
  );
};

export default TodoList;
