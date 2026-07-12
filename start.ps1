Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "      Starting SmilAI Local Servers       " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Start Ollama
Write-Host "1. Booting Ollama (Local AI Engine)..." -ForegroundColor Yellow
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Minimized

# Wait a few seconds for Ollama to spin up
Start-Sleep -Seconds 3

# 2. Start FastAPI Backend
Write-Host "2. Booting FastAPI Backend on Port 8000..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" -ArgumentList "-NoExit -Command `"cd backend; .\.venv\Scripts\Activate.ps1; uvicorn src.python.app.main:app --reload --port 8000`""

# 3. Start React Frontend
Write-Host "3. Booting React Vite Frontend on Port 5173..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" -ArgumentList "-NoExit -Command `"cd frontend; npm run dev`""

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "All services started successfully!" -ForegroundColor Green
Write-Host "Three command windows have been opened for the background processes." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
