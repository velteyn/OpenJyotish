@echo off
chcp 65001 >nul
title Jagannatha Hora — Vedic Astrology

:: Activate venv
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found.
    echo Run install.bat first.
    pause
    exit /b 1
)

:: Launch GUI
python -m jhora --gui
if errorlevel 1 (
    echo.
    echo Something went wrong.
    echo Make sure Python 3.11+ is installed.
    echo Run install.bat first.
    pause
)
