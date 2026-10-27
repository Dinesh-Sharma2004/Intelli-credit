@echo off
echo ========================================
echo   Starting Intelli-Credit Frontend  
echo ========================================
echo.

cd /d "d:\Chronicles\intelli-credit\frontend"

echo Installing React dependencies...
call npm install

echo.
echo Starting frontend development server...
echo Frontend will be available at: http://localhost:3000
echo.

npm run dev

pause
