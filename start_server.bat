@echo off
echo 🚀 Starting RecTransport API Server...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if requirements are installed
echo 📦 Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 📥 Installing requirements...
    pip install -r requirements.txt
)

echo.
echo 🌐 Starting server on http://localhost:8000
echo 📚 API docs: http://localhost:8000/docs
echo 🔧 Health check: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
python start_server.py

pause 