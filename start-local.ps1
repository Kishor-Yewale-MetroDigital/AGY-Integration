$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"

Write-Host "Starting TalentFlow Backend (FastAPI on http://localhost:8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$BackendDir'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"

Write-Host "Starting TalentFlow Frontend (Vite on http://localhost:5173)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$FrontendDir'; npm run dev"

Start-Sleep -Seconds 3
Write-Host "Opening TalentFlow UI at http://localhost:5173 ..." -ForegroundColor Green
Start-Process "http://localhost:5173"
Write-Host "Swagger API Docs available at http://localhost:8000/docs" -ForegroundColor Yellow
