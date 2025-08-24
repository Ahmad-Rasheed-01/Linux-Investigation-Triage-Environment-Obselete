# ============================================================
# LITE - Virtual Environment Activation Helper
# PowerShell Script to ensure virtual environment is activated
# ============================================================

# Function to check and activate virtual environment
function Ensure-VirtualEnvironment {
    param(
        [string]$ProjectRoot = $PSScriptRoot
    )
    
    # Change to project directory if not already there
    if ((Get-Location).Path -ne $ProjectRoot) {
        Write-Host "Changing to project directory: $ProjectRoot" -ForegroundColor Yellow
        Set-Location $ProjectRoot
    }
    
    # Check if we're already in a virtual environment
    $inVirtualEnv = $env:VIRTUAL_ENV -ne $null
    $localVenvExists = Test-Path "venv\Scripts\Activate.ps1"
    
    if ($inVirtualEnv) {
        Write-Host "✅ Virtual environment already active: $env:VIRTUAL_ENV" -ForegroundColor Green
        return $true
    }
    
    if ($localVenvExists) {
        Write-Host "🔄 Activating local virtual environment..." -ForegroundColor Yellow
        try {
            & ".\venv\Scripts\Activate.ps1"
            Write-Host "✅ Virtual environment activated successfully!" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "❌ Failed to activate virtual environment: $_" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "❌ Virtual environment not found at: venv\Scripts\Activate.ps1" -ForegroundColor Red
        Write-Host "Please create virtual environment first:" -ForegroundColor Yellow
        Write-Host "  python -m venv venv" -ForegroundColor Cyan
        Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
        Write-Host "  pip install -r requirements.txt" -ForegroundColor Cyan
        return $false
    }
}

# Auto-activate if script is run directly (not sourced)
if ($MyInvocation.InvocationName -ne '.') {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "LITE - Virtual Environment Activation" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Cyan
    
    $success = Ensure-VirtualEnvironment
    
    if ($success) {
        Write-Host "\n🎉 Ready to work! Virtual environment is active." -ForegroundColor Green
        Write-Host "\nTo use this in other scripts, add this line:" -ForegroundColor Yellow
        Write-Host "  . .\activate_venv.ps1; Ensure-VirtualEnvironment" -ForegroundColor Cyan
    } else {
        Write-Host "\n❌ Virtual environment setup required." -ForegroundColor Red
        exit 1
    }
}

# Function is available when script is dot-sourced