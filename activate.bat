@echo off
REM ============================================================================
REM Quick Activation Script for Existing Virtual Environment
REM Run this if venv is already set up
REM ============================================================================

echo.
echo Activating virtual environment...
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment (venv) activated!
    echo.
    echo You can now run:
    echo   python backend\pipeline.py
    echo.
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Virtual environment (.venv) activated!
    echo.
    echo You can now run:
    echo   python backend\pipeline.py
    echo.
) else (
    echo ERROR: No virtual environment found!
    echo.
    echo To setup virtual environment run:
    echo   setup-windows.bat
    echo.
)

cmd /k
