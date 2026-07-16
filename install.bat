@echo off
title Jagannatha Hora - Setup

echo ========================================
echo  Jagannatha Hora - Installer
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Install Python 3.11+ from https://python.org
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

python -c "import sys; sys.exit(0 if sys.version_info>=(3,11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.11+ required.
    python --version
    pause
    exit /b 1
)
echo Python found.
echo.

if not exist venv\ (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Could not create venv.
        pause
        exit /b 1
    )
    echo Done.
) else (
    echo venv\ already exists. Using it.
)
echo.

echo Activating venv and installing...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Could not activate venv.
    pause
    exit /b 1
)

python -m pip install --upgrade pip -q 2>nul
pip install -r requirements.txt
pip install -e .

echo.
echo ========================================
echo  Setup complete!
echo ========================================
echo.
echo Commands:
echo   run.bat        Launch GUI
echo   jhora tui      Terminal mode
echo   jhora --help   See all CLI commands
echo.
pause
