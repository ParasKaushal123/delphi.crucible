Write-Host "Stopping Backend (port 8000)..." -ForegroundColor Yellow
$backendProcess = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
if ($backendProcess) { 
    Stop-Process -Id $backendProcess -Force 
    Write-Host "Backend stopped." -ForegroundColor Green
} else {
    Write-Host "Backend is not running." -ForegroundColor Gray
}

Write-Host "Stopping Frontend (port 3000)..." -ForegroundColor Yellow
$frontendProcess = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
if ($frontendProcess) { 
    Stop-Process -Id $frontendProcess -Force 
    Write-Host "Frontend stopped." -ForegroundColor Green
} else {
    Write-Host "Frontend is not running." -ForegroundColor Gray
}

Write-Host "Stopping Redis..." -ForegroundColor Yellow
docker-compose down

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All services stopped successfully!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
