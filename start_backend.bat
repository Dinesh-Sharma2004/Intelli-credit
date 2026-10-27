@echo off
setlocal
title Intelli-Credit Backend

echo ========================================
echo   Intelli-Credit Backend
echo ========================================
echo.

cd /d "%~dp0"
set "PYTHON_EXE=C:\Program Files\Python313\python.exe"

if not exist "%PYTHON_EXE%" (
  echo Python not found at %PYTHON_EXE%
  echo Update start_backend.bat with the correct Python path.
  pause
  exit /b 1
)

echo Starting Flask backend on http://127.0.0.1:5000
echo.
"%PYTHON_EXE%" backend\run_flask.py

endlocal
