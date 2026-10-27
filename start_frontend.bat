@echo off
setlocal
title Intelli-Credit Frontend

echo ========================================
echo   Intelli-Credit Frontend
echo ========================================
echo.

cd /d "%~dp0frontend"

if not exist "node_modules" (
  echo node_modules not found. Installing frontend dependencies...
  call npm install
  if errorlevel 1 (
    echo npm install failed.
    pause
    exit /b 1
  )
)

echo Starting Next.js frontend on http://127.0.0.1:3000
echo Backend target: http://127.0.0.1:5000/api/v1
echo.
call npm run dev

endlocal
