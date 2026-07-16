@echo off
chcp 65001 >nul
title Jagannatha Hora — Setup

echo ========================================
echo  Jagannatha Hora — Installer
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Install Python 3.11+ from https://python.org
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

python -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.11+ required. Found:
    python --version
    pause
    exit /b 1
)

echo Python: 
python --version
echo.

:: Create venv
if not exist venv\ (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Could not create venv.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists (venv\).
    echo To recreate: rmdir /s /q venv ^&^& install.bat
    echo.
)

:: Activate and install
call venv\Scripts\activate.bat

echo Installing dependencies...
python -m pip install --upgrade pip -q
pip install -r requirements.txt
pip install -e .

echo.
echo ========================================
echo  Setup complete!
echo ========================================
echo.
echo Commands:
echo   run.bat             Launch GUI
echo   jhora tui           Terminal mode
echo   jhora chart --help  See all CLI commands
echo.
pause
