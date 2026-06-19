# Redis is already running natively on this machine

Write-Host "Starting Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; `$env:PYTHONUTF8=1; uvicorn main:app --port 8000"

Write-Host "Starting Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All services started!" -ForegroundColor Cyan
Write-Host "Backend is running on http://localhost:8000"
Write-Host "Frontend is running on http://localhost:3000"
Write-Host "========================================" -ForegroundColor Cyan
