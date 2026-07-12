@echo off
echo ==========================================
echo       Starting SmilAI Local Servers       
echo ==========================================

echo 1. Booting Ollama (Local AI Engine)...
start "Ollama Engine" /MIN ollama serve

timeout /t 3 /nobreak >nul

echo 2. Booting FastAPI Backend on Port 8000...
start "SmilAI Backend" cmd /k "cd backend && call .\.venv\Scripts\activate.bat && uvicorn src.python.app.main:app --reload --port 8000"

echo 3. Booting React Vite Frontend on Port 5173...
start "SmilAI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo All services started successfully!
echo Close this window to let them run in the background.
echo ==========================================
pause
