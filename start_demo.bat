@echo off
setlocal
title Intelli-Credit Demo Launcher

cd /d "%~dp0"
if not exist "runtime-logs" mkdir "runtime-logs"

echo ========================================
echo   Intelli-Credit Demo Launcher
echo ========================================
echo.
echo This will open two terminals:
echo 1. Flask backend on port 5000
echo 2. Next.js frontend on port 3000
echo.

start "Intelli-Credit Backend" cmd /k ""%~dp0start_backend.bat""
timeout /t 3 /nobreak >nul
start "Intelli-Credit Frontend" cmd /k ""%~dp0start_frontend.bat""

echo Waiting briefly before verification...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify_demo_stack.ps1"

echo.
echo If frontend does not start because of local machine permissions,
echo run the opened frontend terminal as Administrator once.
echo.
pause
endlocal
