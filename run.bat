@echo off
title OpenJyotish

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo venv not found. Run install.bat first.
    pause
    exit /b 1
)

if not exist jhcore\ephe\sepl_18.se1 (
    echo Ephemeris data not found.
    echo Run install.bat to auto-download it.
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
