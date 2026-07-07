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
    echo ERROR: Python not found. Install Python 3.11+ from python.org
    echo Make sure to check "Add Python to PATH" during installation.
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

echo Python OK: 
python --version
echo.

:: Create virtual environment
if exist venv\ (
    echo Virtual environment already exists (venv/).
    echo To recreate, delete the venv folder and run install.bat again.
) else (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Could not create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created.
)

echo.

:: Activate and install
call venv\Scripts\activate

echo Installing dependencies (this may take a minute)...
python -m pip install --upgrade pip -q
pip install -e .
if errorlevel 1 (
    echo.
    echo WARNING: pip install had issues. Trying without editable mode...
    pip install PyQt6 pyswisseph typer rich
)

echo.
echo ========================================
echo  Setup complete!
echo ========================================
echo.
echo To run the app:
echo     run.bat
echo.
echo Or manually:
echo     venv\Scripts\activate ^&^& python -m jhora --gui
echo.
pause
