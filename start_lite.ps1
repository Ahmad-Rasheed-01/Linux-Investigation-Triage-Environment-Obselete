# ============================================================
# LITE - Linux Investigation & Triage Environment
# PowerShell Startup Script for Development Environment
# ============================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "LITE - Linux Investigation & Triage Environment" -ForegroundColor Yellow
Write-Host "Starting Development Environment..." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Change to the script directory
Set-Location $PSScriptRoot

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then run: .\venv\Scripts\Activate.ps1; pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Load environment variables from .env file
Write-Host "Loading environment variables..." -ForegroundColor Green
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
    Write-Host "Environment variables loaded from .env" -ForegroundColor Green
} else {
    Write-Host "Warning: .env file not found, using default settings" -ForegroundColor Yellow
}

# Check if required packages are installed
Write-Host "Checking dependencies..." -ForegroundColor Green
try {
    python -c "import flask, flask_sqlalchemy, flask_migrate" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Dependencies missing"
    }
} catch {
    Write-Host "Installing required packages..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Create uploads directory if it doesn't exist
if (-not (Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting LITE Application..." -ForegroundColor Yellow
Write-Host "Server will be available at: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start the Flask application
try {
    python app.py
} catch {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "Application stopped with an error!" -ForegroundColor Red
    Write-Host "Check the error messages above for troubleshooting." -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}