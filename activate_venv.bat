@echo off
REM ============================================================
REM LITE - Virtual Environment Activation Helper
REM Batch Script to ensure virtual environment is activated
REM ============================================================

setlocal enabledelayedexpansion

REM Change to the script directory
cd /d "%~dp0"

REM Check if we're already in a virtual environment
if defined VIRTUAL_ENV (
    echo ✅ Virtual environment already active: %VIRTUAL_ENV%
    goto :success
)

REM Check if local virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found at: venv\Scripts\activate.bat
    echo Please create virtual environment first:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r requirements.txt
    exit /b 1
)

REM Activate virtual environment
echo 🔄 Activating local virtual environment...
call venv\Scripts\activate.bat

if defined VIRTUAL_ENV (
    echo ✅ Virtual environment activated successfully!
    goto :success
) else (
    echo ❌ Failed to activate virtual environment
    exit /b 1
)

:success
echo.
echo 🎉 Ready to work! Virtual environment is active.
echo.
echo To use this in other scripts, add this line:
echo   call activate_venv.bat
echo.
exit /b 0