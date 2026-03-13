@echo off
REM Exam AI setup script for Windows

echo ================================
echo Exam AI Setup
echo ================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not on PATH.
    pause
    exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed or not on PATH.
    pause
    exit /b 1
)

echo Python and Node.js detected.
echo.

echo Setting up backend...
cd backend

if not exist "venv" (
    python -m venv venv
)

call venv\Scripts\activate.bat

if not exist ".env" (
    copy .env.example .env >nul
    echo Created backend\.env from backend\.env.example
    echo Update these values before running the app:
    echo   - MONGODB_URL
    echo   - OPENROUTER_API_KEY
    echo   - OPENROUTER_MODEL
    echo   - SECRET_KEY
)

pip install -r requirements.txt

echo.
echo Setting up frontend...
cd ..\frontend
call npm install

echo.
echo ================================
echo Setup complete
echo ================================
echo.
echo Start the backend:
echo   cd backend
echo   venv\Scripts\activate
echo   uvicorn app.main:app --reload --port 8000
echo.
echo Start the frontend in another terminal:
echo   cd frontend
echo   npm run dev
echo.
echo App URL: http://localhost:5173
echo API docs: http://localhost:8000/docs
echo.
pause
