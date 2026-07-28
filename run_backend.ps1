# OmniVision v1.0 - Backend Run Script (Windows)

Write-Host "OmniVision v1.0 - Starting Enterprise Backend..." -ForegroundColor Cyan
Set-Location $PSScriptRoot

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

& ".\venv\Scripts\Activate.ps1"
pip install -r requirements-base.txt --quiet

Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Health:   http://localhost:8000/api/v1/health" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000 (run separately)" -ForegroundColor Yellow
Write-Host ""

uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
