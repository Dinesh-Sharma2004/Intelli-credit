#!/bin/bash
# ============================================================================
# Quick Activation Script for Existing Virtual Environment
# Run this if venv is already set up
# ============================================================================

echo ""
echo "Activating virtual environment..."
echo ""

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment (venv) activated!"
    echo ""
    echo "You can now run:"
    echo "  python backend/pipeline.py"
    echo ""
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Virtual environment (.venv) activated!"
    echo ""
    echo "You can now run:"
    echo "  python backend/pipeline.py"
    echo ""
else
    echo "ERROR: No virtual environment found!"
    echo ""
    echo "To setup virtual environment run:"
    echo "  bash setup-linux.sh"
    echo ""
fi
