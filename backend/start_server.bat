@echo off
echo ========================================
echo   Starting Intelli-Credit Backend
echo ========================================
echo.

cd /d "d:\Chronicles\intelli-credit\backend"

echo Installing Node.js dependencies...
call npm install

echo.
echo Starting backend server on http://127.0.0.1:8000
echo.
echo Backend will handle:
echo   - Document upload and processing
echo   - OCR text extraction  
echo   - File management
echo   - API endpoints
echo.

node server.js

pause
