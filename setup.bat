@echo off
REM Exam AI - Complete Startup Script for Windows

echo ================================
echo Exam AI - Complete Setup ^& Start
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed. Please install Python 3.9+
    pause
    exit /b 1
)

REM Check if Node is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed. Please install Node.js 16+
    pause
    exit /b 1
)

echo Python and Node.js are installed
echo.

REM Setup Backend
echo Installing backend dependencies...
cd backend

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

if not exist ".env" (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo Please edit backend\.env with your actual settings:
    echo   - MONGODB_URL
    echo   - OPENAI_API_KEY
    echo   - SECRET_KEY
)

echo Installing backend dependencies...
pip install -r requirements.txt >nul 2>&1

echo Backend setup complete
echo.

REM Setup Frontend
echo Installing frontend dependencies...
cd ..\frontend

if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install >nul 2>&1
)

echo Frontend setup complete
echo.

REM Summary
echo ================================
echo Setup Complete!
echo ================================
echo.
echo To start the application:
echo.
echo 1. Start Backend (in terminal 1):
echo    cd backend
echo    venv\Scripts\activate
echo    uvicorn app.main:app --reload --port 8000
echo.
echo 2. Start Frontend (in terminal 2):
echo    cd frontend
echo    npm run dev
echo.
echo 3. Access the app at http://localhost:5173
echo    API docs: http://localhost:8000/docs
echo.
echo Default test credentials:
echo    Email: test@example.com
echo    Password: test123
echo.
pause
