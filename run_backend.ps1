# OmniVision — Phase 1 Run Scripts (Windows)

Write-Host "OmniVision Phase 1 — Starting Backend..." -ForegroundColor Cyan
Set-Location $PSScriptRoot

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

& ".\venv\Scripts\Activate.ps1"
pip install -r requirements.txt --quiet

Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "In a second terminal run: .\run_frontend.ps1" -ForegroundColor Yellow
Write-Host ""

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
