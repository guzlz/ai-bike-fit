# AI Bike Fit - one-command setup for Windows (PowerShell)
#
#   Right-click -> Run with PowerShell, or from a terminal:
#       powershell -ExecutionPolicy Bypass -File setup.ps1
#
# Installs uv (if missing), all Python dependencies, and ffmpeg (if missing).
# After this, run:  uv run python analyze_bikefit.py --input my-ride.mov --out out_fit

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "== AI Bike Fit setup ==" -ForegroundColor Cyan

# 1. uv (installs and manages Python 3.12 automatically)
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..." -ForegroundColor Yellow
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
}
Write-Host "uv OK" -ForegroundColor Green

# 2. Python deps (ultralytics, supervision, opencv, numpy, torch...) from the lockfile
Write-Host "Installing Python dependencies (this pulls PyTorch, ~1-2 min)..." -ForegroundColor Yellow
uv sync
Write-Host "Dependencies OK" -ForegroundColor Green

# 3. ffmpeg
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "Installing ffmpeg via winget..." -ForegroundColor Yellow
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
    Write-Host "ffmpeg installed - RESTART your terminal so it's on PATH." -ForegroundColor Green
} else {
    Write-Host "ffmpeg OK" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. Now run:" -ForegroundColor Cyan
Write-Host "  uv run python analyze_bikefit.py --input my-ride.mov --out out_fit" -ForegroundColor White
