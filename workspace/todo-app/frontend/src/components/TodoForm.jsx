import React, { useState } from 'react';

const TodoForm = ({ onAddTodo }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!title.trim()) {
      setError('Title is required');
      return;
    }

    try {
      await onAddTodo({ title: title.trim(), description: description.trim() || null });
      setTitle('');
      setDescription('');
      setError('');
    } catch (err) {
      setError(err.message || 'Failed to add todo');
    }
  };

  return (
    <form className="todo-form" onSubmit={handleSubmit}>
      {error && <div className="error-message">{error}</div>}
      <div className="form-group">
        <input
          type="text"
          placeholder="What needs to be done?"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="form-input"
        />
      </div>
      <div className="form-group">
        <input
          type="text"
          placeholder="Description (optional)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="form-input"
        />
      </div>
      <button type="submit" className="btn btn-primary">
        ➕ Add Todo
      </button>
    </form>
  );
};

export default TodoForm;
