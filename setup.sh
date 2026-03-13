#!/bin/bash
# Exam AI setup script

set -e

echo "================================"
echo "Exam AI Setup"
echo "================================"

authoritative_python() {
    if command -v python3 >/dev/null 2>&1; then
        echo python3
    elif command -v python >/dev/null 2>&1; then
        echo python
    else
        echo ""
    fi
}

PYTHON_BIN=$(authoritative_python)
if [ -z "$PYTHON_BIN" ]; then
    echo "Python is not installed or not on PATH."
    exit 1
fi

if ! command -v node >/dev/null 2>&1; then
    echo "Node.js is not installed or not on PATH."
    exit 1
fi

echo "Python and Node.js detected."
echo ""

echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    "$PYTHON_BIN" -m venv venv
fi

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    source venv/Scripts/activate
fi

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created backend/.env from backend/.env.example"
    echo "Update these values before running the app:"
    echo "  - MONGODB_URL"
    echo "  - OPENROUTER_API_KEY"
    echo "  - OPENROUTER_MODEL"
    echo "  - SECRET_KEY"
fi

pip install -r requirements.txt

echo ""
echo "Setting up frontend..."
cd ../frontend
npm install

echo ""
echo "================================"
echo "Setup complete"
echo "================================"
echo ""
echo "Start the backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo "Start the frontend in another terminal:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "App URL: http://localhost:5173"
echo "API docs: http://localhost:8000/docs"
