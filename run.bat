@echo off
chcp 65001 >nul
title Jagannatha Hora — Vedic Astrology

:: Check for virtual environment
if exist venv\Scripts\python.exe (
    call venv\Scripts\activate
) else if exist .venv\Scripts\python.exe (
    call .venv\Scripts\activate
)

:: Launch GUI
python -m jhora --gui
if errorlevel 1 (
    echo.
    echo Something went wrong. Make sure Python 3.11+ is installed.
    echo Run install.bat first to set up dependencies.
    pause
)
