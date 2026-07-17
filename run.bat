@echo off
title OpenJyotish

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo venv not found. Run install.bat first.
    pause
    exit /b 1
)

python -m jhora --gui
if errorlevel 1 (
    echo.
    echo Error launching GUI.
    echo Try running install.bat again.
    pause
)
