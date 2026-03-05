#!/bin/bash
# Exam AI - Complete Startup Script

echo "================================"
echo "Exam AI - Complete Setup & Start"
echo "================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+"
    exit 1
fi

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+"
    exit 1
fi

echo ""
echo "✓ Python and Node.js are installed"
echo ""

# Setup Backend
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit backend/.env with your actual settings:"
    echo "   - MONGODB_URL"
    echo "   - OPENAI_API_KEY"
    echo "   - SECRET_KEY"
fi

echo "Installing backend dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

echo "✓ Backend setup complete"
echo ""

# Setup Frontend
echo "📦 Setting up frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install > /dev/null 2>&1
fi

echo "✓ Frontend setup complete"
echo ""

# Summary
echo "================================"
echo "✓ Setup Complete!"
echo "================================"
echo ""
echo "To start the application:"
echo ""
echo "1️⃣  Start Backend (in terminal 1):"
echo "   cd backend"
echo "   source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
echo "   uvicorn app.main:app --reload --port 8000"
echo ""
echo "2️⃣  Start Frontend (in terminal 2):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3️⃣  Access the app at http://localhost:5173"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "Default test credentials:"
echo "   Email: test@example.com"
echo "   Password: test123"
echo ""
