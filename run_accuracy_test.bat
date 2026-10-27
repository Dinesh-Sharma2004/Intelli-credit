@echo off
REM ============================================================================
REM Run OCR Model Accuracy Test on Dataset (Windows)
REM ============================================================================

setlocal

echo.
echo ============================================================================
echo OCR Model Accuracy Testing - Dataset Evaluation
echo ============================================================================
echo.

REM Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found
    echo Run: setup-windows.bat
    pause
    exit /b 1
)

REM Change to backend directory
cd backend

REM Run accuracy test
echo Running accuracy test...
echo.
python test_accuracy.py

if errorlevel 1 (
    echo.
    echo ERROR: Test failed
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo Results saved to: backend\model_accuracy_report.json
echo ============================================================================
echo.
pause
