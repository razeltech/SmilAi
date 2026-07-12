@echo off
echo ==========================================
echo       Starting SmilAI Local Servers       
echo ==========================================

echo 1. Booting Ollama (Local AI Engine)...
start "Ollama Engine" /MIN ollama serve

echo    Waiting for Ollama to initialize...
timeout /t 5 /nobreak >nul

REM Health check — confirm Ollama is reachable before starting backend
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    [WARNING] Ollama may not be running. Chat will use fallback mode.
) else (
    echo    [OK] Ollama is ready.
)

echo 2. Booting FastAPI Backend on Port 8000...
start "SmilAI Backend" cmd /k "cd backend && call .\.venv\Scripts\activate.bat && set PYTHONPATH=%cd%\.venv\Lib\site-packages && python -m uvicorn src.python.app.main:app --reload --host 0.0.0.0 --port 8000"

echo 3. Booting React Vite Frontend on Port 5173...
start "SmilAI Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo All services started successfully!
echo   Backend:  http://localhost:8000/docs
echo   Frontend: http://localhost:5173
echo   Ollama:   http://localhost:11434
echo ==========================================
echo Close this window to let them run in the background.
pause
