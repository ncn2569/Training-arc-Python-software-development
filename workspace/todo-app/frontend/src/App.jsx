import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import TodoForm from './components/TodoForm';
import TodoList from './components/TodoList';
import Filter from './components/Filter';
import Stats from './components/Stats';
import { todoAPI } from './api/todoAPI';
import './App.css';

function App() {
  const [todos, setTodos] = useState([]);
  const [stats, setStats] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTodos = useCallback(async (filter = 'all') => {
    try {
      setLoading(true);
      let completedParam = null;
      if (filter === 'completed') completedParam = true;
      if (filter === 'pending') completedParam = false;
      const data = await todoAPI.getAllTodos(completedParam);
      setTodos(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch todos');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const data = await todoAPI.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, []);

  useEffect(() => {
    fetchTodos(activeFilter);
    fetchStats();
  }, [activeFilter, fetchTodos, fetchStats]);

  const addTodo = async (todoData) => {
    try {
      const newTodo = await todoAPI.createTodo(todoData);
      setTodos((prev) => [newTodo, ...prev]);
      await fetchStats();
    } catch (err) {
      throw err;
    }
  };

  const toggleTodo = async (id) => {
    const todo = todos.find((t) => t.id === id);
    if (!todo) return;
    try {
      const updated = await todoAPI.updateTodo(id, { completed: !todo.completed });
      setTodos((prev) =>
        prev.map((t) => (t.id === id ? updated : t))
      );
      await fetchStats();
    } catch (err) {
      throw err;
    }
  };

  const deleteTodo = async (id) => {
    try {
      await todoAPI.deleteTodo(id);
      setTodos((prev) => prev.filter((t) => t.id !== id));
      await fetchStats();
    } catch (err) {
      throw err;
    }
  };

  const updateTodo = async (id, todoData) => {
    try {
      const updated = await todoAPI.updateTodo(id, todoData);
      setTodos((prev) =>
        prev.map((t) => (t.id === id ? updated : t))
      );
      await fetchStats();
    } catch (err) {
      throw err;
    }
  };

  const handleFilterChange = (filter) => {
    setActiveFilter(filter);
  };

  if (error && !todos.length) {
    return (
      <div className="error-container">
        <div className="error-content">
          <span className="error-icon">⚠️</span>
          <h2>Connection Error</h2>
          <p>Could not connect to the API server.</p>
          <p>Please check if the backend server is running.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Header />
      <main className="main-content">
        <div className="content-wrapper">
          <Stats stats={stats} />
          <TodoForm onAddTodo={addTodo} />
          <Filter activeFilter={activeFilter} onFilterChange={handleFilterChange} />
          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              <p>Loading todos...</p>
            </div>
          ) : (
            <TodoList
              todos={todos}
              onToggleTodo={toggleTodo}
              onDeleteTodo={deleteTodo}
              onUpdateTodo={updateTodo}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
