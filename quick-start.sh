#!/bin/bash

# Intelli-Credit Installation and Testing Script for macOS/Linux

echo "🚀 Intelli-Credit Advanced OCR & Modern Frontend Setup"
echo "======================================================"
echo ""

# Check Python installation
echo "📍 Checking Python..."
python3 --version

# Setup Python virtual environment if needed
if [ ! -d "backend/venv" ]; then
    echo "📍 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    cd ..
else
    source backend/venv/bin/activate
fi

# Install/update backend dependencies
echo "📍 Installing backend dependencies..."
pip install -r backend/requirements_fixed.txt -q

# Move to frontend
cd frontend

# Install frontend dependencies
echo "📍 Installing frontend dependencies..."
npm install -q 2>/dev/null || npm install

# Move back to root
cd ..

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Starting Services..."
echo "========================"
echo ""

# Start backend
echo "📍 Starting Backend API (Port 8000)..."
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

sleep 3

# Start frontend
echo "📍 Starting Frontend (Port 3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Services started successfully!"
echo ""
echo "🌐 Access Points:"
echo "  - Frontend:    http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs:    http://localhost:8000/docs"
echo "  - CAM Page:    http://localhost:3000/cam-generator"
echo ""
echo "📊 Test OCR with Indian Languages:"
echo "  POST /api/ocr/advanced"
echo "  Languages: hi, te, kn, gu, bn, ml, en"
echo ""
echo "💾 Generated Documents:"
echo "  - CAM files: ./generated_cams/"
echo ""
echo "Press Ctrl+C to stop the servers"
echo ""

# Keep script running
wait

