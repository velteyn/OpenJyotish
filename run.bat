@echo off
title Jagannatha Hora

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found.
    echo Run install.bat first.
    pause
    exit /b 1
)

python -m jhora --gui
if errorlevel 1 (
    echo.
    echo Something went wrong. Run install.bat first.
    pause
)
