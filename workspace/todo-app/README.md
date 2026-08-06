# 📝 Todo App - Fullstack Application

A modern fullstack Todo application built with **React + Vite** (Frontend), **FastAPI** (Backend), **SQLite** (Database), and deployed with **Docker Compose**.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose                          │
├──────────────────┬──────────────────────────────────────────┤
│   Frontend       │   Backend                                │
│   React + Vite   │   FastAPI + SQLAlchemy                   │
│   :5173          │   :8000                                  │
│                  │   SQLite Database                        │
└──────────────────┴──────────────────────────────────────────┘
```

## ✨ Features

- ✅ Create, Read, Update, Delete (CRUD) todos
- 🔍 Filter by completed/pending status
- 📊 Dashboard statistics
- 📱 Responsive design
- 🎨 Modern UI with gradient backgrounds
- ⚡ Hot module replacement (HMR) with Vite
- 🐳 Docker Compose deployment

## 📁 Project Structure

```
todo-app/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI application
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── database.py      # Database configuration
│   │   ├── crud.py          # CRUD operations
│   │   └── tests/           # Backend tests
│   │       ├── test_api.py
│   │       └── test_crud.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pytest.ini
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx          # Main App component
│   │   ├── main.jsx         # Entry point
│   │   ├── App.css          # App styles
│   │   ├── index.css        # Global styles
│   │   ├── api/             # API services
│   │   └── components/      # React components
│   ├── package.json
│   ├── Dockerfile
│   └── vite.config.js
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose installed
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Option 1: Docker Compose Deployment (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd todo-app

# Build and start containers
docker-compose up --build

# The application will be available at:
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🧪 Running Tests

### Backend Tests

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend

# Install test dependencies
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom

# Run tests
npm run test

# Run tests in watch mode
npm run test -- --watch
```

## 📡 API Endpoints

| Method | Endpoint              | Description              |
|--------|-----------------------|--------------------------|
| GET    | `/`                   | Root endpoint            |
| GET    | `/todos`              | Get all todos            |
| GET    | `/todos/{id}`         | Get todo by ID           |
| POST   | `/todos`              | Create new todo          |
| PUT    | `/todos/{id}`         | Update todo              |
| DELETE | `/todos/{id}`         | Delete todo              |
| GET    | `/todos/stats`        | Get todo statistics      |

### Query Parameters

- `completed` (bool): Filter by completed status
- `skip` (int): Number of records to skip (pagination)
- `limit` (int): Maximum number of records to return

## 🎨 Screenshots

(Add screenshots here if available)

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=sqlite:///./data/todo.db
SECRET_KEY=your-secret-key-here
```

### Docker Compose Configuration

Edit `docker-compose.yml` to customize:

- Port mappings
- Volume mounts
- Environment variables
- Network settings

## 🐳 Docker Commands

```bash
# Build and start
docker-compose up --build

# Start in detached mode
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild and start
docker-compose up --build -d

# Remove all containers and volumes
docker-compose down -v
```

## 📝 Development Guidelines

### Backend

- Use Pydantic v2 for request/response validation
- Follow RESTful API conventions
- Implement proper error handling
- Write comprehensive tests

### Frontend

- Use functional components with hooks
- Implement proper loading/error states
- Use CSS modules or styled-components
- Follow component composition best practices

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

Nguyen's AI Agent - Autonomous Terminal AI Engineer

## 📞 Support

For support, please open an issue in the repository.

---

**Happy coding! 🚀**
