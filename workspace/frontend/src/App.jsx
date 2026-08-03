import { useState, useEffect } from 'react'

const API = '/api/todos'

function App() {
  const [todos, setTodos] = useState([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editTitle, setEditTitle] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all')

  const fetchTodos = async () => {
    try {
      setLoading(true)
      const res = await fetch(API)
      const data = await res.json()
      setTodos(data)
    } catch (err) {
      setError('Failed to load todos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchTodos() }, [])

  const addTodo = async (e) => {
    e.preventDefault()
    if (!title.trim()) return
    try {
      const res = await fetch(API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title.trim(), description: description.trim() })
      })
      if (res.ok) { setTitle(''); setDescription(''); fetchTodos() }
    } catch { setError('Failed to add todo') }
  }

  const toggleTodo = async (id, completed) => {
    await fetch(`${API}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ completed: !completed })
    })
    fetchTodos()
  }

  const deleteTodo = async (id) => {
    await fetch(`${API}/${id}`, { method: 'DELETE' })
    fetchTodos()
  }

  const startEdit = (todo) => {
    setEditingId(todo.id)
    setEditTitle(todo.title)
    setEditDesc(todo.description)
  }

  const saveEdit = async (id) => {
    const body = {}
    if (editTitle) body.title = editTitle
    if (editDesc !== undefined) body.description = editDesc
    await fetch(`${API}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    setEditingId(null)
    fetchTodos()
  }

  const filtered = todos.filter(t => {
    if (filter === 'active') return !t.completed
    if (filter === 'completed') return t.completed
    return true
  })

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: 20, fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ textAlign: 'center', color: '#333' }}>✅ Todo App</h1>

      {error && <p style={{ color: 'red', textAlign: 'center' }}>{error}</p>}

      <form onSubmit={addTodo} style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 20 }}>
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="Task title..."
          style={{ padding: 10, fontSize: 16, border: '1px solid #ccc', borderRadius: 6 }}
        />
        <input
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="Description (optional)..."
          style={{ padding: 10, fontSize: 14, border: '1px solid #ccc', borderRadius: 6 }}
        />
        <button type="submit" style={{
          padding: 12, fontSize: 16, backgroundColor: '#4CAF50', color: '#fff',
          border: 'none', borderRadius: 6, cursor: 'pointer'
        }}>+ Add Todo</button>
      </form>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {['all', 'active', 'completed'].map(f => (
          <button key={f} onClick={() => setFilter(f)} style={{
            padding: '6px 14px', border: '1px solid #ccc', borderRadius: 20,
            backgroundColor: filter === f ? '#4CAF50' : '#fff',
            color: filter === f ? '#fff' : '#333', cursor: 'pointer',
            textTransform: 'capitalize'
          }}>{f} ({f === 'all' ? todos.length : f === 'active' ? todos.filter(t => !t.completed).length : todos.filter(t => t.completed).length})</button>
        ))}
      </div>

      {loading ? <p style={{ textAlign: 'center' }}>Loading...</p> : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {filtered.length === 0 && <p style={{ textAlign: 'center', color: '#999' }}>No todos found 🎉</p>}
          {filtered.map(todo => (
            <li key={todo.id} style={{
              display: 'flex', alignItems: 'center', gap: 10, padding: 12,
              marginBottom: 8, backgroundColor: todo.completed ? '#f0f0f0' : '#fff',
              border: '1px solid #eee', borderRadius: 8
            }}>
              <input type="checkbox" checked={todo.completed}
                onChange={() => toggleTodo(todo.id, todo.completed)}
                style={{ width: 20, height: 20, cursor: 'pointer' }} />
              {editingId === todo.id ? (
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <input value={editTitle} onChange={e => setEditTitle(e.target.value)}
                    style={{ padding: 6, fontSize: 14, border: '1px solid #ccc', borderRadius: 4 }} />
                  <input value={editDesc} onChange={e => setEditDesc(e.target.value)}
                    style={{ padding: 6, fontSize: 12, border: '1px solid #ccc', borderRadius: 4 }} />
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button onClick={() => saveEdit(todo.id)} style={{
                      padding: '4px 10px', backgroundColor: '#4CAF50', color: '#fff',
                      border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 12
                    }}>Save</button>
                    <button onClick={() => setEditingId(null)} style={{
                      padding: '4px 10px', backgroundColor: '#999', color: '#fff',
                      border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 12
                    }}>Cancel</button>
                  </div>
                </div>
              ) : (
                <div style={{ flex: 1, cursor: 'pointer' }} onClick={() => startEdit(todo)}>
                  <div style={{
                    textDecoration: todo.completed ? 'line-through' : 'none',
                    color: todo.completed ? '#999' : '#333', fontWeight: 500
                  }}>{todo.title}</div>
                  {todo.description && <div style={{ fontSize: 12, color: '#777', marginTop: 2 }}>{todo.description}</div>}
                </div>
              )}
              <button onClick={() => deleteTodo(todo.id)} style={{
                padding: '6px 12px', backgroundColor: '#f44336', color: '#fff',
                border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 12
              }}>Delete</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default App
