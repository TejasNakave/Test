@echo off
echo 🚀 Setting up Trade Assistant RAG Chatbot...
echo.

REM Check Node.js
echo 📋 Checking prerequisites...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js 18+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Node.js found
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.11+ from https://python.org/
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Python found
)

echo.
echo 📦 Installing dependencies...

REM Install frontend dependencies
echo 🎯 Installing frontend dependencies...
call npm install
if errorlevel 1 (
    echo ❌ Frontend setup failed. Please check your Node.js installation.
    pause
    exit /b 1
)
echo ✅ Frontend dependencies installed

REM Install backend dependencies
echo 🐍 Installing backend dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Backend setup failed. Please check your Python installation.
    echo Try: pip install --upgrade pip
    pause
    exit /b 1
)
echo ✅ Backend dependencies installed

REM Check for .env file
echo.
echo 🔑 Setting up environment...
if not exist ".env" (
    echo ⚠️  Creating .env file from template...
    copy .env.example .env
    echo.
    echo 🔑 IMPORTANT: Please edit .env file and add your OpenAI API key!
    echo    File location: %CD%\.env
    echo    Required: LLM_API_KEY=your_openai_api_key_here
    echo.
    echo Opening .env file for editing...
    notepad .env
) else (
    echo ✅ .env file already exists
)

echo.
echo ✅ Setup complete!
echo.
echo 🚀 To start the application:
echo.
echo 1. Backend (in one terminal):
echo    python rag_server.py
echo.
echo 2. Frontend (in another terminal):
echo    npm start
echo.
echo 🌐 Then open: http://localhost:3000
echo 📖 API docs: http://localhost:8000/docs
echo.
echo 📚 For troubleshooting, check README.md
echo.
pause