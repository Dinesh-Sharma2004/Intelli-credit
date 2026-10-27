# Quick Start with Existing Virtual Environment

This guide assumes you already have a virtual environment set up.

## Activation

### Windows
```bash
activate.bat
```

### Linux/Mac
```bash
source activate.sh
```

## Verify Installation

After activation, verify all dependencies are installed:

```bash
python -c "import torch; print(f'✓ PyTorch {torch.__version__}')"
python -c "import transformers; print(f'✓ Transformers {transformers.__version__}')"
python -c "import sqlalchemy; print(f'✓ SQLAlchemy')"
```

## Run Pipeline

```bash
# From project root (with venv activated)
python backend/pipeline.py
```

## Dataset Location

Images are located in:
```
backend/Dataset/verified_twice/{language}/
```

Available languages:
- assamese
- gujarati
- hindi
- kannada
- malayalam
- marathi
- odia
- punjabi
- tamil
- telugu
- urdu

## Python Usage

```python
from backend.pipeline import DocumentProcessingPipeline

# Initialize
pipeline = DocumentProcessingPipeline(device='cpu')

# Process image
result = pipeline.process_document('backend/Dataset/verified_twice/hindi/0_gt.txt')

# Or process entire dataset
dataset_results = pipeline.process_dataset()

# Get stats
stats = pipeline.get_statistics()

# Cleanup
pipeline.cleanup()
```

## Troubleshooting

### Models Not Found
```bash
cd backend
git clone https://github.com/AI4Bharat/IndicTrOCR models/indic_trocr
git clone https://github.com/AI4Bharat/IndicTrans2 models/indictrans2
cd ..
```

### Missing Dependencies
```bash
pip install -r backend/requirements.txt
```

### Database Connection
```bash
# Start PostgreSQL
# Then set DATABASE_URL
export DATABASE_URL=postgresql://postgres:password@localhost:5432/intelli_credit
```

## Next Steps

1. ✅ Virtual environment is active
2. ✅ Dependencies installed
3. ✅ Dataset available at `backend/Dataset/verified_twice/`
4. Run: `python backend/pipeline.py`

For detailed documentation, see:
- [QUICKSTART_OCR_PIPELINE.md](QUICKSTART_OCR_PIPELINE.md)
- [SETUP_GUIDE_OCR_PIPELINE.md](SETUP_GUIDE_OCR_PIPELINE.md)
- [OCR_PIPELINE_README.md](OCR_PIPELINE_README.md)
