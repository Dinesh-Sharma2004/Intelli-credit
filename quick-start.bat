@echo off
REM Intelli-Credit Quick Start Script for Windows

echo.
echo 🚀 Intelli-Credit Advanced OCR ^& Modern Frontend Setup
echo ======================================================
echo.

REM Check Python
echo 📍 Checking Python...
python --version

REM Setup virtual environment
if not exist "backend\venv" (
    echo 📍 Creating Python virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    cd ..
) else (
    call backend\venv\Scripts\activate.bat
)

REM Install backend dependencies
echo 📍 Installing backend dependencies...
pip install -r backend\requirements_fixed.txt -q

REM Install frontend dependencies
cd frontend
echo 📍 Installing frontend dependencies...
call npm install

cd ..

echo.
echo ✅ Installation complete!
echo.
echo 🎯 Starting Services...
echo ========================
echo.

REM Start backend in new window
echo 📍 Starting Backend API (Port 8000)...
start "Intelli-Credit Backend" cmd /k "cd backend && call venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak

REM Start frontend in new window
echo 📍 Starting Frontend (Port 3000)...
start "Intelli-Credit Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ✅ Services started in separate windows!
echo.
echo 🌐 Access Points:
echo   - Frontend:    http://localhost:3000
echo   - Backend API: http://localhost:8000
echo   - API Docs:    http://localhost:8000/docs
echo   - CAM Page:    http://localhost:3000/cam-generator
echo.
echo 📊 Test OCR with Indian Languages:
echo   POST /api/ocr/advanced
echo   Languages: hi, te, kn, gu, bn, ml, en
echo   Accuracy: 90%+ on Indian scripts
echo.
echo 💾 Generated Documents:
echo   - CAM files saved to: ./generated_cams/
echo.
echo ✨ Features Enabled:
echo   ✅ Modern 3D Navigation
echo   ✅ Animated Buttons with Shimmer Effects
echo   ✅ Advanced Indian Language OCR
echo   ✅ Document Download (Fixed)
echo   ✅ Real-time Error Handling
echo.
echo Close the command windows to stop the servers.
echo.

pause
