import axios from 'axios';

const API_URL = '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const todoAPI = {
  // Get all todos
  getAllTodos: async (completed = null) => {
    const params = {};
    if (completed !== null) {
      params.completed = completed;
    }
    const response = await api.get('/todos', { params });
    return response.data;
  },

  // Get a single todo
  getTodo: async (id) => {
    const response = await api.get(`/todos/${id}`);
    return response.data;
  },

  // Create a new todo
  createTodo: async (todoData) => {
    const response = await api.post('/todos', todoData);
    return response.data;
  },

  // Update a todo
  updateTodo: async (id, todoData) => {
    const response = await api.put(`/todos/${id}`, todoData);
    return response.data;
  },

  // Delete a todo
  deleteTodo: async (id) => {
    const response = await api.delete(`/todos/${id}`);
    return response.data;
  },

  // Get todo statistics
  getStats: async () => {
    const response = await api.get('/todos/stats');
    return response.data;
  },
};

export default api;
