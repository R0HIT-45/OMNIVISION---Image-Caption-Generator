# OmniVision — Phase 1 Frontend (Windows)

Set-Location $PSScriptRoot

if (Test-Path "venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
}

Write-Host "OmniVision Frontend: http://localhost:8501" -ForegroundColor Cyan
streamlit run frontend/app.py --server.port 8501
