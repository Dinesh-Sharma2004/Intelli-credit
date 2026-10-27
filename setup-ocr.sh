#!/bin/bash

# ====================================================
# IndicTrOCR + IndicTrans2 Setup Script for Linux/Mac
# ====================================================

set -e

echo ""
echo "===================================================="
echo "  IndicTrOCR + IndicTrans2 Automatic Setup"
echo "===================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 is not installed"
    echo ""
    echo "Please install Python 3.9+ first:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-venv python3-pip"
    echo "  macOS: brew install python3"
    exit 1
fi

python3 --version
echo "✓ Python 3 is installed"

# Navigate to backend directory
cd "$(dirname "$0")/backend" || exit 1
echo "✓ Current directory: $(pwd)"

# Check if virtual environment exists
if [ ! -d "../intelli_venv" ]; then
    echo ""
    echo "[1/4] Creating Python virtual environment..."
    python3 -m venv ../intelli_venv
    if [ $? -ne 0 ]; then
        echo "✗ Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "[2/4] Activating virtual environment..."
source ../intelli_venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "[3/4] Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "[4/4] Installing dependencies..."
echo "This may take 5-10 minutes on first install..."
echo ""

pip install -r requirements_fixed.txt
if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Failed to install dependencies"
    exit 1
fi

echo ""
echo "✓ Dependencies installed successfully"

# Download models
echo ""
echo "===================================="
echo "  Downloading AI Models"
echo "===================================="
echo ""
echo "This will download ~10GB of models from HuggingFace"
echo "This may take 20-60 minutes depending on your internet speed"
echo ""

python setup_models.py
if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Failed to download models"
    echo "Please check your internet connection and try again"
    exit 1
fi

echo ""
echo "===================================================="
echo "  ✓ Setup Complete!"
echo "===================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Start the backend:"
echo "   cd backend"
echo "   python main.py"
echo ""
echo "2. In another terminal, start the frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Open your browser to http://localhost:3000"
echo ""
echo "===================================================="
echo ""
