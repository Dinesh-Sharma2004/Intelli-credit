#!/bin/bash
# ============================================================================
# Virtual Environment Setup Script for Linux/Mac
# Multilingual Document Processing Pipeline
# ============================================================================

set -e  # Exit on error

echo ""
echo "============================================================================"
echo "Multilingual Document Processing Pipeline - Virtual Environment Setup"
echo "============================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Step 1: Checking Python installation..."
python3 --version
echo ""

# Create virtual environment
echo "Step 2: Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists at: venv"
    echo "Using existing environment..."
elif [ -d ".venv" ]; then
    echo "Virtual environment already exists at: .venv"
    echo "Using existing environment..."
    venv_dir=".venv"
else
    echo "Creating new virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created successfully!"
    venv_dir="venv"
fi
echo ""

# Activate virtual environment
echo "Step 3: Activating virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    venv_dir="venv"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    venv_dir=".venv"
else
    echo "ERROR: No virtual environment found"
    exit 1
fi
echo "Virtual environment activated!"
echo ""

# Upgrade pip
echo "Step 4: Upgrading pip..."
python -m pip install --upgrade pip
echo ""

# Install requirements
echo "Step 5: Installing dependencies..."
echo "This may take several minutes..."
echo ""
pip install -r backend/requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    echo "Check your internet connection and try again"
    exit 1
fi
echo "Dependencies installed successfully!"
echo ""

# Clone models
echo "Step 6: Cloning AI models..."
echo ""

if [ -d "backend/models/indic_trocr" ]; then
    echo "IndicTrOCR already exists, skipping..."
else
    echo "Cloning IndicTrOCR model..."
    git clone https://github.com/AI4Bharat/IndicTrOCR backend/models/indic_trocr || {
        echo "WARNING: Failed to clone IndicTrOCR"
        echo "You can clone it manually later using:"
        echo "  git clone https://github.com/AI4Bharat/IndicTrOCR backend/models/indic_trocr"
    }
fi
echo ""

if [ -d "backend/models/indictrans2" ]; then
    echo "IndicTrans2 already exists, skipping..."
else
    echo "Cloning IndicTrans2 model..."
    git clone https://github.com/AI4Bharat/IndicTrans2 backend/models/indictrans2 || {
        echo "WARNING: Failed to clone IndicTrans2"
        echo "You can clone it manually later using:"
        echo "  git clone https://github.com/AI4Bharat/IndicTrans2 backend/models/indictrans2"
    }
fi
echo ""

# Setup environment file
echo "Step 7: Creating environment configuration..."
if [ -f "backend/.env" ]; then
    echo ".env file already exists, skipping..."
else
    echo "Creating .env file from template..."
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo ".env file created from template"
    else
        cat > backend/.env << 'EOF'
# Backend Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/intelli_credit
INFERENCE_DEVICE=cpu
LOG_LEVEL=INFO
EOF
        echo ".env file created with default settings"
    fi
fi
echo ""

# Verify installation
echo "Step 8: Verifying installation..."
cd backend
python -c "import torch; print(f'PyTorch {torch.__version__}: OK')" || echo "WARNING: PyTorch check failed"
python -c "import transformers; print(f'Transformers {transformers.__version__}: OK')" || echo "WARNING: Transformers check failed"
python -c "import sqlalchemy; print(f'SQLAlchemy {sqlalchemy.__version__}: OK')" || echo "WARNING: SQLAlchemy check failed"
cd ..
echo ""

# Print next steps
echo "============================================================================"
echo "Setup Complete!"
echo "============================================================================"
echo ""
echo "Virtual Environment Location: $(pwd)/venv"
echo ""
echo "Next Steps:"
echo "-----------"
echo ""
echo "1. To activate virtual environment in future:"
echo "   source venv/bin/activate"
echo ""
echo "2. To run the pipeline:"
echo "   python backend/pipeline.py"
echo ""
echo "3. To run tests:"
echo "   python backend/test_pipeline.py"
echo ""
echo "4. Dataset Location:"
echo "   backend/Dataset/verified_twice/{language}/"
echo "   Available languages: hindi, tamil, telugu, gujarati, kannada, malayalam,"
echo "                        marathi, punjabi, urdu, assamese, odia"
echo ""
echo "5. Important: Make sure PostgreSQL is running if using database features"
echo "   Set DATABASE_URL in backend/.env if using custom database"
echo ""
echo "6. For model installation (if cloning failed):"
echo "   git clone https://github.com/AI4Bharat/IndicTrOCR backend/models/indic_trocr"
echo "   git clone https://github.com/AI4Bharat/IndicTrans2 backend/models/indictrans2"
echo ""
echo "Documentation:"
echo "---------------"
echo "- Quick Start: QUICKSTART_OCR_PIPELINE.md"
echo "- Full Setup: SETUP_GUIDE_OCR_PIPELINE.md"
echo "- Configuration: backend/.env.example"
echo ""
echo "============================================================================"
echo ""
