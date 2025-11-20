@echo off
echo Starting ChatGPT-like Proactive Chatbot...
echo.

echo [1/2] Starting FastAPI Backend Server...
start "Backend Server" /min cmd /k "cd /d "%~dp0" && python -m api.app"

echo [2/2] Waiting for backend to start, then launching React Frontend...
timeout /t 3 /nobreak >nul

start "Frontend Server" /min cmd /k "cd /d "%~dp0" && npm start"

echo.
echo ✅ ChatGPT-like Proactive Chatbot is starting up!
echo.
echo 🔗 Backend API: http://localhost:8000
echo 🌐 Frontend App: http://localhost:3000  
echo 📖 API Docs: http://localhost:8000/docs
echo.
echo 🚀 Features:
echo   - ChatGPT-like conversation interface
echo   - Proactive AI suggestions and insights
echo   - User behavior analysis and patterns
echo   - Context-aware conversation management
echo   - Vector database integration
echo   - Real-time response streaming
echo.
echo Both servers are starting in separate windows.
echo Wait about 30 seconds for both to fully load, then go to:
echo http://localhost:3000
echo.
echo Press any key to close this window...
pause >nul