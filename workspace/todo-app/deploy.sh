#!/bin/bash
echo "🚀 Deploying Todo App..."
cd "$(dirname "$0")"
docker-compose up --build -d
echo ""
echo "✅ Deploy complete!"
echo "📱 Frontend: http://localhost:5173"
echo "📡 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 docker-compose ps"
docker-compose ps
