@echo off
title OpenJyotish - Setup

echo ========================================
echo  OpenJyotish - Installer
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Install Python 3.11+ from https://python.org
    echo Make sure to check "Add to PATH" during install.
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

echo Checking ephemeris data...
if not exist jhcore\ephe\sepl_18.se1 (
    echo Ephemeris data not found. Auto-downloading...
    if exist download_ephe.sh (
        bash download_ephe.sh 2>nul
    )
    if not exist jhcore\ephe\sepl_18.se1 (
        python -c "import urllib.request,os;os.makedirs('jhcore/ephe',exist_ok=True);[urllib.request.urlretrieve(f'https://www.astro.com/ftp/swisseph/ephe/{f}','jhcore/ephe/'+f.split('/')[-1]) for f in ['sepl_18.se1','sepl_24.se1','sepl_30.se1','sepl_36.se1','sepl_42.se1','sepl_48.se1','sepl_54.se1','sepl_60.se1','sepl_66.se1','sepl_72.se1','sepl_78.se1','sepl_84.se1','sepl_90.se1','sepl_96.se1','sepl_102.se1','sepl_108.se1','sepl_114.se1','sepl_120.se1','sepl_126.se1','sepl_132.se1','semo_18.se1','semo_24.se1','semo_30.se1','semo_36.se1','semo_42.se1','semo_48.se1','semo_54.se1','semo_60.se1','semo_66.se1','semo_72.se1','semo_78.se1','semo_84.se1','semo_90.se1','semo_96.se1','semo_102.se1','semo_108.se1','semo_114.se1','semo_120.se1','semo_126.se1','semo_132.se1']]" 2>nul
    )
    if exist jhcore\ephe\sepl_18.se1 (
        echo Ephemeris data downloaded.
    ) else (
        echo WARNING: Could not auto-download ephemeris data.
        echo Download from: https://www.astro.com/ftp/swisseph/ephe/
        echo Place .se1 files in jhcore\ephe\
    )
) else (
    echo Ephemeris data found.
)
echo.

echo Cleaning cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
echo Done.
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
echo   jhora --help   All commands
echo.
pause
