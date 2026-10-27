# Multilingual Document Processing Pipeline

A complete end-to-end AI pipeline for processing Indian financial documents with multilingual text extraction, translation, field extraction, and accuracy evaluation.

## Overview

This system processes Indian financial documents (GST invoices, bank statements, annual reports, legal notices) containing multilingual text across 11 Indian languages plus English using state-of-the-art AI models.

### Key Features

- **Multilingual OCR**: Extract text from images in Hindi, Telugu, Tamil, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Urdu, and English
- **Machine Translation**: Translate Indian language text to English using IndicTrans2
- **Field Extraction**: Automatically extract structured financial data (invoice numbers, dates, amounts, GST numbers, etc.)
- **Database Storage**: Store results in PostgreSQL with full audit trail
- **Accuracy Evaluation**: Compute CER (Character Error Rate) and WER (Word Error Rate) metrics
- **Production-Ready**: Clean, modular, well-documented Python code
- **Scalable**: Batch processing, GPU acceleration, multi-worker support

## Project Structure

```
backend/
├── models/                          # AI models (local storage)
│   ├── indic_trocr/               # IndicTrOCR model
│   └── indictrans2/               # IndicTrans2 model
│
├── datasets/                        # Evaluation dataset
│   └── indic_ocr_dataset/
│       ├── images/                # Document images
│       └── labels/                # Ground truth labels
│
├── modules/                         # Production modules
│   ├── __init__.py
│   ├── ocr_module.py              # OCR extraction
│   ├── translation_module.py      # Machine translation
│   ├── extraction_module.py       # Field extraction
│   ├── database_module.py         # PostgreSQL operations
│   └── evaluation_module.py       # Accuracy metrics
│
├── pipeline.py                      # Main orchestration
├── requirements.txt                 # Dependencies
└── .env.example                     # Configuration template
```

## Technology Stack

- **Python 3.8+**
- **PyTorch 2.1+** - Deep learning framework
- **Transformers 4.35+** - HuggingFace models
- **IndicTrOCR** - Multilingual OCR model
- **IndicTrans2** - Multilingual translation model
- **PostgreSQL 13+** - Database
- **SQLAlchemy 2.0+** - ORM
- **OpenCV** - Image processing
- **Pillow** - Image I/O

## Installation

### 1. Quick Activation of Existing Virtual Environment

```bash
# Windows
activate.bat

# Linux/Mac
source activate.sh
```

### 2. Initial Setup (if venv doesn't exist)

```bash
# Windows
setup-windows.bat

# Linux/Mac
bash setup-linux.sh
```

### 3. Clone Models

```bash
cd backend

# Clone IndicTrOCR
git clone https://github.com/AI4Bharat/IndicTrOCR models/indic_trocr

# Clone IndicTrans2
git clone https://github.com/AI4Bharat/IndicTrans2 models/indictrans2

cd ..
```

### 2. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Setup Database (Optional)

```bash
# Ensure PostgreSQL is running
# Create database and set DATABASE_URL
export DATABASE_URL=postgresql://user:password@localhost:5432/intelli_credit
```

## Usage

### Quick Start

```python
from backend.pipeline import DocumentProcessingPipeline

# Initialize pipeline
pipeline = DocumentProcessingPipeline(device='cpu')

# Process document
result = pipeline.process_document('path/to/invoice.png')

# Process batch
results = pipeline.process_batch(['img1.png', 'img2.png'])

# Get statistics
stats = pipeline.get_statistics()

# Cleanup
pipeline.cleanup()
```

### Command Line

```bash
cd backend
python pipeline.py
```

### Module Usage

Each module can be used independently:

```python
# OCR
from backend.modules import IndicTrOCR
ocr = IndicTrOCR()
result = ocr.extract_text('image.png')

# Translation
from backend.modules import IndicTranslator
translator = IndicTranslator()
result = translator.translate("कुल राशि ₹1,25,000", source_lang='hin')

# Extraction
from backend.modules import FinancialFieldExtractor
extractor = FinancialFieldExtractor()
result = extractor.extract_fields(text)

# Database
from backend.modules import DatabaseManager
db = DatabaseManager()
doc_id = db.insert_document(original_text, translated_text, extracted_data)

# Evaluation
from backend.modules import OCREvaluator
evaluator = OCREvaluator()
cer = evaluator.compute_cer(hypothesis, reference)
```

## Processing Pipeline

For each document:

```
Document Image
    ↓
[OCR] Extract multilingual text using IndicTrOCR
    ↓
[DISPLAY] Show detected text in console
    ↓
[TRANSLATION] Translate to English using IndicTrans2
    ↓
[NORMALIZATION] Normalize text (lowercase, standardize formats)
    ↓
[EXTRACTION] Extract structured fields (invoice #, date, amount, GST #, etc.)
    ↓
[DATABASE] Store in PostgreSQL with audit trail
    ↓
[EVALUATION] Compute OCR accuracy metrics (CER, WER) using ground truth
    ↓
Results JSON
```

## Output Example

```json
{
  "image_path": "invoice.png",
  "timestamp": "2024-04-12T10:30:45.123456",
  "ocr_result": {
    "raw_text": [
      "कुल राशि ₹1,25,000",
      "तारीख 12-04-2024"
    ],
    "language_detected": ["hin", "eng"]
  },
  "translation_result": {
    "translated_text": "Total amount ₹1,25,000 Date 12-04-2024"
  },
  "extraction_result": {
    "total_amount": 125000,
    "invoice_date": "2024-04-12",
    "document_type": "invoice"
  },
  "database_result": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "evaluation_result": {
    "cer": 0.04,
    "wer": 0.08
  }
}
```

## Supported Languages

| Code | Language | Script |
|------|----------|--------|
| hin | Hindi | Devanagari |
| tel | Telugu | Telugu |
| tam | Tamil | Tamil |
| ben | Bengali | Bengali |
| mar | Marathi | Devanagari |
| guj | Gujarati | Gujarati |
| kan | Kannada | Kannada |
| mal | Malayalam | Malayalam |
| pan | Punjabi | Gurmukhi |
| urd | Urdu | Arabic/Persian |
| eng | English | Latin |

## Extracted Fields

The pipeline automatically extracts:

- **company_name** - Organization name
- **invoice_number** - Invoice/bill reference number
- **invoice_date** - Date (standardized to YYYY-MM-DD)
- **total_amount** - Total invoice amount (float)
- **gst_number** - GST registration number (GSTIN)
- **bank_account** - Bank account number
- **transaction_amount** - Transaction value
- **transaction_date** - Transaction date
- **document_type** - Detected document type (invoice, bank_statement, etc.)

## API Reference

### IndicTrOCR

```python
ocr = IndicTrOCR(model_path=None, device='cuda')
result = ocr.extract_text(image_path)  # Dict with raw_text, language_detected
results = ocr.extract_text_batch(image_paths)  # List of results
```

### IndicTranslator

```python
translator = IndicTranslator(model_path=None, device='cuda')
result = translator.translate(text, source_lang='hin', target_lang='eng')
result = translator.detect_and_translate(text, target_lang='eng')
results = translator.translate_batch(texts, source_lang='hin')
```

### FinancialFieldExtractor

```python
extractor = FinancialFieldExtractor()
result = extractor.extract_fields(text)  # FinancialExtraction object
text_normalized = extractor.normalize_text(text)
```

### DatabaseManager

```python
db = DatabaseManager(database_url=None)
doc_id = db.insert_document(original_text, translated_text, extracted_data, image_path)
doc = db.get_document(doc_id)
docs = db.get_all_documents(limit=100, offset=0)
results = db.search_documents(gst_number='...', invoice_date='...')
updated = db.update_document(doc_id, **updates)
deleted = db.delete_document(doc_id)
stats = db.get_statistics()
```

### OCREvaluator

```python
evaluator = OCREvaluator(dataset_path=None)
ground_truth = evaluator.load_ground_truth(image_name)
cer = evaluator.compute_cer(hypothesis, reference)
wer = evaluator.compute_wer(hypothesis, reference)
result = evaluator.evaluate_single_document(image_name, ocr_text)
summary = evaluator.evaluate_dataset(ocr_results)
```

### DocumentProcessingPipeline

```python
pipeline = DocumentProcessingPipeline(device='cuda')
result = pipeline.process_document(image_path, source_language='hin')
results = pipeline.process_batch(image_paths)
dataset_results = pipeline.process_dataset()
stats = pipeline.get_statistics()
pipeline.save_results(output_path)
pipeline.cleanup()
```

## Database Schema

```sql
CREATE TABLE extracted_financial_documents (
    document_id UUID PRIMARY KEY,
    original_language_text TEXT,
    translated_english_text TEXT,
    invoice_number VARCHAR(255),
    invoice_date DATE,
    total_amount FLOAT,
    gst_number VARCHAR(15),
    bank_account VARCHAR(255),
    transaction_amount FLOAT,
    transaction_date DATE,
    company_name VARCHAR(255),
    document_type VARCHAR(50),
    source_image_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/intelli_credit

# Models
INDIC_TROCR_PATH=backend/models/indic_trocr
INDICTRANS2_PATH=backend/models/indictrans2

# GPU
CUDA_VISIBLE_DEVICES=0
INFERENCE_DEVICE=cuda

# Processing
BATCH_SIZE=32
SOURCE_LANGUAGE=hin
TARGET_LANGUAGE=eng
```

See `.env.example` for comprehensive configuration options.

## Performance

### Benchmarks (Approximate)

| Task | CPU | GPU |
|------|-----|-----|
| OCR (single page) | 30-60s | 5-10s |
| Translation (page) | 5-10s | 1-2s |
| Field Extraction | <1s | <1s |
| Database Insert | 10-50ms | 10-50ms |
| Batch (10 pages) | 300-600s | 40-100s |

### Memory Requirements

- **Minimum**: 4GB RAM (CPU)
- **Recommended**: 16GB RAM + 6GB GPU VRAM
- **Models**: ~3GB (OCR) + ~2GB (Translation)

## Accuracy Metrics

The evaluation module computes:

- **CER (Character Error Rate)**: Percentage of character-level differences
  - Formula: (substitutions + deletions + insertions) / reference_length
  - Target: < 5% for production quality

- **WER (Word Error Rate)**: Percentage of word-level differences
  - Formula: (substitutions + deletions + insertions) / reference_words
  - Target: < 10% for production quality

## Dataset Format

To evaluate accuracy, the dataset is already structured:

```
backend/Dataset/verified_twice/
├── assamese/
│   ├── 0_gt.txt
│   ├── 1_gt.txt
│   └── (image files)
├── gujarati/
├── hindi/
├── kannada/
├── malayalam/
├── marathi/
├── odia/
├── punjabi/
├── tamil/
├── telugu/
└── urdu/
```

Each language directory contains:
- Ground truth text files (*.txt)
- Corresponding document images

The evaluation module automatically processes this structure.

## Troubleshooting

### Models Not Found

```bash
git clone https://github.com/AI4Bharat/IndicTrOCR backend/models/indic_trocr
git clone https://github.com/AI4Bharat/IndicTrans2 backend/models/indictrans2
```

### Database Connection Failed

```bash
# Check PostgreSQL
psql -U postgres -d intelli_credit

# Set DATABASE_URL
export DATABASE_URL=postgresql://user:pass@localhost:5432/db
```

### Out of Memory

```python
# Use CPU
pipeline = DocumentProcessingPipeline(device='cpu')

# Or process smaller batches
pipeline.process_batch(images[:5])
```

### CUDA Not Available

```python
# Use CPU automatically
import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
pipeline = DocumentProcessingPipeline(device=device)
```

## Documentation

- **[QUICKSTART_OCR_PIPELINE.md](QUICKSTART_OCR_PIPELINE.md)** - 5-minute quick start guide
- **[SETUP_GUIDE_OCR_PIPELINE.md](SETUP_GUIDE_OCR_PIPELINE.md)** - Detailed setup instructions
- **[backend/.env.example](backend/.env.example)** - Configuration options

## Module Documentation

Each module has comprehensive docstrings:

- **[backend/modules/ocr_module.py](backend/modules/ocr_module.py)** - OCR extraction
- **[backend/modules/translation_module.py](backend/modules/translation_module.py)** - Translation
- **[backend/modules/extraction_module.py](backend/modules/extraction_module.py)** - Field extraction
- **[backend/modules/database_module.py](backend/modules/database_module.py)** - Database operations
- **[backend/modules/evaluation_module.py](backend/modules/evaluation_module.py)** - Accuracy evaluation
- **[backend/pipeline.py](backend/pipeline.py)** - Pipeline orchestration

## References

- **IndicTrOCR**: https://github.com/AI4Bharat/IndicTrOCR
- **IndicTrans2**: https://github.com/AI4Bharat/IndicTrans2
- **AI4Bharat**: https://ai4bharat.org/
- **PyTorch**: https://pytorch.org/
- **Transformers**: https://huggingface.co/transformers/

## License

This pipeline uses open-source models from AI4Bharat. Please refer to their repositories for licensing information.

## Contributing

Improvements welcome! Areas for enhancement:

- [ ] Support for more Indian languages
- [ ] Improved financial field extraction patterns
- [ ] Real-time processing server (FastAPI)
- [ ] Web UI for document upload and review
- [ ] Fine-tuning with domain-specific data
- [ ] Performance optimizations

## Support

For issues or questions:

1. Check the [documentation](SETUP_GUIDE_OCR_PIPELINE.md)
2. Review module [docstrings](backend/modules/)
3. Check [IndicTrOCR issues](https://github.com/AI4Bharat/IndicTrOCR/issues)
4. Check [IndicTrans2 issues](https://github.com/AI4Bharat/IndicTrans2/issues)

---

**Ready to process documents?** Start with the [QUICKSTART_OCR_PIPELINE.md](QUICKSTART_OCR_PIPELINE.md) guide!
