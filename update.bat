@echo off
chcp 65001 >nul
title Jagannatha Hora — Update

echo ========================================
echo  Pulling latest changes...
echo ========================================
git pull
if errorlevel 1 (
    echo ERROR: git pull failed. Make sure Git is installed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Reinstalling...
echo ========================================
if exist venv\Scripts\python.exe (
    call venv\Scripts\activate
    pip install -e . --quiet
) else if exist .venv\Scripts\python.exe (
    call .venv\Scripts\activate
    pip install -e . --quiet
) else (
    echo No virtual environment found. Run install.bat first.
    pause
    exit /b 1
)

echo.
echo Update complete. Run run.bat to start.
pause
