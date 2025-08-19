@echo off
REM ============================================================
REM LITE - Linux Investigation & Triage Environment
REM Startup Script for Development Environment
REM ============================================================

echo ============================================================
echo LITE - Linux Investigation ^& Triage Environment
echo Starting Development Environment...
echo ============================================================
echo.

REM Change to the project directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Load environment variables from .env file
echo Loading environment variables...
if exist ".env" (
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        if not "%%a"=="" if not "%%a:~0,1"=="#" (
            set "%%a=%%b"
        )
    )
    echo Environment variables loaded from .env
) else (
    echo Warning: .env file not found, using default settings
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import flask, flask_sqlalchemy, flask_migrate" 2>nul
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
)

REM Create uploads directory if it doesn't exist
if not exist "uploads" mkdir uploads

echo.
echo ============================================================
echo Starting LITE Application...
echo Server will be available at: http://127.0.0.1:5000
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

REM Start the Flask application
python app.py

REM Keep the window open if there's an error
if errorlevel 1 (
    echo.
    echo ============================================================
    echo Application stopped with an error!
    echo Check the error messages above for troubleshooting.
    echo ============================================================
    pause
)