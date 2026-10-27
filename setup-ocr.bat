@echo off
REM ====================================================
REM  IndicTrOCR + IndicTrans2 Setup Script for Windows
REM  This script automates the entire setup process
REM ====================================================

setlocal enabledelayedexpansion

echo.
echo ====================================================
echo  IndicTrOCR + IndicTrans2 Automatic Setup
echo ====================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python is not installed or not in PATH
    echo.
    echo Please install Python 3.9+ from https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✓ Python is installed

REM Navigate to backend directory
cd /d "%~dp0backend" || exit /b 1
echo ✓ Current directory: %CD%

REM Check if virtual environment exists
if not exist "..\intelli_venv\" (
    echo.
    echo [1/4] Creating Python virtual environment...
    python -m venv ..\intelli_venv
    if errorlevel 1 (
        echo ✗ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment
echo.
echo [2/4] Activating virtual environment...
call ..\intelli_venv\Scripts\activate.bat
if errorlevel 1 (
    echo ✗ Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual environment activated

REM Upgrade pip
echo.
echo [3/4] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
echo ✓ pip upgraded

REM Install dependencies
echo.
echo [4/4] Installing dependencies...
echo This may take 5-10 minutes on first install...
echo.

pip install -r requirements_fixed.txt
if errorlevel 1 (
    echo.
    echo ✗ Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ✓ Dependencies installed successfully

REM Download models
echo.
echo ====================================
echo  Downloading AI Models
echo ====================================
echo.
echo This will download ~10GB of models from HuggingFace
echo This may take 20-60 minutes depending on your internet speed
echo.

python setup_models.py
if errorlevel 1 (
    echo.
    echo ✗ Failed to download models
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo ====================================================
echo  ✓ Setup Complete!
echo ====================================================
echo.
echo Next steps:
echo.
echo 1. Start the backend:
echo    cd backend
echo    python main.py
echo.
echo 2. In another terminal, start the frontend:
echo    cd frontend
echo    npm run dev
echo.
echo 3. Open your browser to http://localhost:3000
echo.
echo ====================================================
echo.

pause
