@echo off
REM ============================================================================
REM Virtual Environment Setup Script for Windows
REM Multilingual Document Processing Pipeline
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo Multilingual Document Processing Pipeline - Virtual Environment Setup
echo ============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo Step 1: Checking Python installation...
python --version
echo.

REM Create virtual environment
echo Step 2: Creating virtual environment...
if exist venv (
    echo Virtual environment already exists at: venv
    echo Using existing environment...
) else if exist .venv (
    echo Virtual environment already exists at: .venv
    echo Using existing environment...
    set venv=.venv
) else (
    echo Creating new virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
)
echo.

REM Activate virtual environment
echo Step 3: Activating virtual environment...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    set venv=.venv
) else (
    echo ERROR: No virtual environment found
    echo Check for venv or .venv directory
    pause
    exit /b 1
)
echo Virtual environment activated!
echo.

REM Upgrade pip
echo Step 4: Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: pip upgrade encountered issues, continuing anyway...
)
echo.

REM Install requirements
echo Step 5: Installing dependencies...
echo This may take several minutes...
echo.
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Check your internet connection and try again
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

REM Clone models
echo Step 6: Cloning AI models...
echo.

if exist backend\models\indic_trocr (
    echo IndicTrOCR already exists, skipping...
) else (
    echo Cloning IndicTrOCR model...
    git clone https://github.com/AI4Bharat/IndicTrOCR backend\models\indic_trocr
    if errorlevel 1 (
        echo WARNING: Failed to clone IndicTrOCR
        echo You can clone it manually later using:
        echo   git clone https://github.com/AI4Bharat/IndicTrOCR backend\models\indic_trocr
    )
)
echo.

if exist backend\models\indictrans2 (
    echo IndicTrans2 already exists, skipping...
) else (
    echo Cloning IndicTrans2 model...
    git clone https://github.com/AI4Bharat/IndicTrans2 backend\models\indictrans2
    if errorlevel 1 (
        echo WARNING: Failed to clone IndicTrans2
        echo You can clone it manually later using:
        echo   git clone https://github.com/AI4Bharat/IndicTrans2 backend\models\indictrans2
    )
)
echo.

REM Setup environment file
echo Step 7: Creating environment configuration...
if exist backend\.env (
    echo .env file already exists, skipping...
) else (
    echo Creating .env file from template...
    if exist backend\.env.example (
        copy backend\.env.example backend\.env >nul
        echo .env file created from template
    ) else (
        echo.
        echo # Backend Configuration > backend\.env
        echo DATABASE_URL=postgresql://postgres:password@localhost:5432/intelli_credit >> backend\.env
        echo INFERENCE_DEVICE=cpu >> backend\.env
        echo LOG_LEVEL=INFO >> backend\.env
        echo.
        echo .env file created with default settings
    )
)
echo.

REM Verify installation
echo Step 8: Verifying installation...
cd backend
python -c "import torch; print(f'PyTorch {torch.__version__}: OK')"
python -c "import transformers; print(f'Transformers {transformers.__version__}: OK')"
python -c "import sqlalchemy; print(f'SQLAlchemy {sqlalchemy.__version__}: OK')"
cd ..
echo.

REM Print next steps
echo ============================================================================
echo Setup Complete!
echo ============================================================================
echo.
echo Virtual Environment Location: %CD%\venv
echo.
echo Next Steps:
echo -----------
echo.
echo 1. To activate virtual environment in future:
echo    venv\Scripts\activate.bat
echo.
echo 2. To run the pipeline:
echo    python backend\pipeline.py
echo.
echo 3. To run tests:
echo    python backend\test_pipeline.py
echo.
echo 4. Dataset Location:
echo    backend\Dataset\verified_twice\{language}\
echo    Available languages: hindi, tamil, telugu, gujarati, kannada, malayalam,
echo                         marathi, punjabi, urdu, assamese, odia
echo.
echo 5. Important: Make sure PostgreSQL is running if using database features
echo    Set DATABASE_URL in backend\.env if using custom database
echo.
echo 6. For model installation (if cloning failed):
echo    git clone https://github.com/AI4Bharat/IndicTrOCR backend\models\indic_trocr
echo    git clone https://github.com/AI4Bharat/IndicTrans2 backend\models\indictrans2
echo.
echo Documentation:
echo ---------------
echo - Quick Start: QUICKSTART_OCR_PIPELINE.md
echo - Full Setup: SETUP_GUIDE_OCR_PIPELINE.md
echo - Configuration: backend\.env.example
echo.
echo ============================================================================
echo.
pause
