@echo off
echo Installing Jagannatha Hora...
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

:: Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create venv
    pause
    exit /b 1
)

:: Activate and install
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install -e ".[gui]"
if %errorlevel% neq 0 (
    pip install PyQt6 pyswisseph typer rich
)
if %errorlevel% neq 0 (
    echo Install failed
    pause
    exit /b 1
)

echo.
echo Done. Run run.bat to start.
pause
