import React, { useState } from 'react';

const TodoItem = ({ todo, onToggle, onDelete, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(todo.title);
  const [editDescription, setEditDescription] = useState(todo.description || '');
  const [error, setError] = useState('');

  const handleSave = async () => {
    if (!editTitle.trim()) {
      setError('Title is required');
      return;
    }
    try {
      await onUpdate(todo.id, {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
      });
      setIsEditing(false);
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to update todo');
    }
  };

  const handleCancel = () => {
    setEditTitle(todo.title);
    setEditDescription(todo.description || '');
    setIsEditing(false);
    setError('');
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isEditing) {
    return (
      <div className={`todo-item todo-item-editing ${todo.completed ? 'completed' : ''}`}>
        <div className="todo-edit-content">
          <div className="form-group">
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="form-input"
              autoFocus
            />
          </div>
          <div className="form-group">
            <input
              type="text"
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              className="form-input"
              placeholder="Description"
            />
          </div>
          {error && <div className="error-message">{error}</div>}
          <div className="todo-actions">
            <button onClick={handleSave} className="btn btn-save">💾 Save</button>
            <button onClick={handleCancel} className="btn btn-cancel">❌ Cancel</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`todo-item ${todo.completed ? 'completed' : ''}`}>
      <div className="todo-content">
        <input
          type="checkbox"
          checked={todo.completed}
          onChange={() => onToggle(todo.id)}
          className="todo-checkbox"
        />
        <div className="todo-text">
          <h3 className={`todo-title ${todo.completed ? 'line-through' : ''}`}>
            {todo.title}
          </h3>
          {todo.description && (
            <p className="todo-description">{todo.description}</p>
          )}
          <span className="todo-date">{formatDate(todo.created_at)}</span>
        </div>
      </div>
      <div className="todo-actions">
        <button
          onClick={() => setIsEditing(true)}
          className="btn btn-edit"
          title="Edit"
        >
          ✏️
        </button>
        <button
          onClick={() => onDelete(todo.id)}
          className="btn btn-delete"
          title="Delete"
        >
          🗑️
        </button>
      </div>
    </div>
  );
};

export default TodoItem;
