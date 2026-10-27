#!/bin/bash
# ============================================================================
# Run OCR Model Accuracy Test on Dataset (Linux/Mac)
# ============================================================================

echo ""
echo "============================================================================"
echo "OCR Model Accuracy Testing - Dataset Evaluation"
echo "============================================================================"
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "ERROR: Virtual environment not found"
    echo "Run: bash setup-linux.sh"
    exit 1
fi

# Change to backend directory
cd backend

# Run accuracy test
echo "Running accuracy test..."
echo ""
python test_accuracy.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Test failed"
    exit 1
fi

echo ""
echo "============================================================================"
echo "Results saved to: backend/model_accuracy_report.json"
echo "============================================================================"
echo ""
