# One-command backend launcher (Windows PowerShell).
# Creates a venv on first run, installs deps, then starts the API with reload.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

& ".\.venv\Scripts\Activate.ps1"

Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -q -r requirements.txt

if (-not (Test-Path ".env")) {
    Write-Host "No .env found - copying .env.example (remember to add a real OPENAI_API_KEY)." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

Write-Host "Starting API on http://localhost:8000 ..." -ForegroundColor Green
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
