"""
Quick Start Guide for Multilingual Document Processing Pipeline

Fast-track setup and usage instructions.
"""

# ============================================================================
# QUICK START GUIDE
# ============================================================================

## 5-MINUTE SETUP

### Step 1: Activate Virtual Environment
```bash
# Windows
activate.bat

# Linux/Mac
source activate.sh
```

If virtual environment doesn't exist, run setup first:
```bash
# Windows
setup-windows.bat

# Linux/Mac
bash setup-linux.sh
```

### Step 2: Install Models
```bash
cd backend

# Clone IndicTrOCR
git clone https://github.com/AI4Bharat/IndicTrOCR models/indic_trocr

# Clone IndicTrans2
git clone https://github.com/AI4Bharat/IndicTrans2 models/indictrans2

cd ..
```

### Step 2: Install Models
```bash
cd backend

# Clone IndicTrOCR
git clone https://github.com/AI4Bharat/IndicTrOCR models/indic_trocr

# Clone IndicTrans2
git clone https://github.com/AI4Bharat/IndicTrans2 models/indictrans2

cd ..
```

### Step 3: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 4: Setup Database (Optional)
```bash
# PostgreSQL must be running
# Default connection: postgresql://postgres:password@localhost:5432/intelli_credit

# Or set custom connection:
export DATABASE_URL=postgresql://user:pass@host:5432/db
```

### Step 4: Add Test Images
```bash
# Images are already in:
backend/Dataset/verified_twice/{language}

# Available languages:
# hindi, tamil, telugu, gujarati, kannada, malayalam,
# marathi, punjabi, urdu, assamese, odia
```

## BASIC USAGE

### Python Script
```python
from backend.pipeline import DocumentProcessingPipeline

# Create pipeline (uses CPU if GPU unavailable)
pipeline = DocumentProcessingPipeline(device='cpu')

# Process single document
result = pipeline.process_document(
    'backend/datasets/indic_ocr_dataset/images/invoice.png'
)

# Print results
print(result)

# Cleanup
pipeline.cleanup()
```

### Command Line
```bash
cd backend
python pipeline.py
```

## EXAMPLE OUTPUT

```
====================================================================
Processing document: invoice.png
====================================================================

==============================================================
Processing image: invoice.png
==============================================================
Detected OCR text:
------------------------------------------------------
कुल राशि ₹1,25,000
तारीख 12-04-2024
जीएसटी संख्या 27AABCT1234H1Z0
------------------------------------------------------

==============================================================
Translation: Hindi → English
==============================================================
Original (Hindi):
------------------------------------------------------
कुल राशि ₹1,25,000
तारीख 12-04-2024
------------------------------------------------------
Translated (English):
------------------------------------------------------
Total amount ₹1,25,000
Date 12-04-2024
------------------------------------------------------

==============================================================
Extracted Structured Data
==============================================================
total_amount: 125000
invoice_date: 2024-04-12
gst_number: 27AABCT1234H1Z0
document_type: invoice

==============================================================
Database Insertion Confirmation
==============================================================
Document ID: 550e8400-e29b-41d4-a716-446655440000
Invoice Number: None
Invoice Date: 2024-04-12
Total Amount: ₹125,000.00
Company Name: None
Document Type: invoice
Created At: 2024-04-12 10:30:45.123456

==============================================================
OCR Accuracy Evaluation: invoice.png
==============================================================
CER (Character Error Rate): 0.0400 (4.00%)
WER (Word Error Rate): 0.0800 (8.00%)

====================================================================
DOCUMENT PROCESSING COMPLETE
====================================================================

Processing Steps Status:
------------------------------------------------------
✓ OCR: SUCCESS
✓ Translation: SUCCESS
✓ Extraction: SUCCESS
✓ Database: SUCCESS
✓ Evaluation: SUCCESS
```

## BATCH PROCESSING

```python
from backend.pipeline import DocumentProcessingPipeline

pipeline = DocumentProcessingPipeline(device='cpu')

# Process multiple images
images = [
    'backend/datasets/indic_ocr_dataset/images/invoice1.png',
    'backend/datasets/indic_ocr_dataset/images/invoice2.png',
    'backend/datasets/indic_ocr_dataset/images/invoice3.png',
]

results = pipeline.process_batch(images)

# Process entire dataset
dataset_results = pipeline.process_dataset()

# Get statistics
stats = pipeline.get_statistics()
print(f"Processed: {stats['total_documents_processed']} documents")
print(f"Average CER: {stats['ocr_metrics']['average_cer']:.4f}")
print(f"Average WER: {stats['ocr_metrics']['average_wer']:.4f}")

# Save results
pipeline.save_results('results.json')

pipeline.cleanup()
```

## INDIVIDUAL MODULE USAGE

### OCR Only
```python
from backend.modules import IndicTrOCR

ocr = IndicTrOCR(device='cpu')
result = ocr.extract_text('image.png')
print(result['raw_text'])
```

### Translation Only
```python
from backend.modules import IndicTranslator

translator = IndicTranslator(device='cpu')
result = translator.translate(
    "कुल राशि ₹1,25,000",
    source_lang='hin',
    target_lang='eng'
)
print(result['translated_text'])
```

### Field Extraction Only
```python
from backend.modules import FinancialFieldExtractor

extractor = FinancialFieldExtractor()
result = extractor.extract_fields(
    "Invoice: INV-001\nDate: 12-04-2024\nAmount: ₹1,25,000"
)
print(result.to_dict())
```

### Database Only
```python
from backend.modules import DatabaseManager

db = DatabaseManager()

# Insert
doc_id = db.insert_document(
    original_text="Original text",
    translated_text="Translated text",
    extracted_data={'invoice_number': 'INV-001'},
    source_image_path='path/to/image.png'
)

# Query
doc = db.get_document(doc_id)
print(doc)

# Search
results = db.search_documents(invoice_number='INV-001')
print(results)

# Stats
stats = db.get_statistics()
print(stats)
```

### Evaluation Only
```python
from backend.modules import OCREvaluator

evaluator = OCREvaluator()

cer = evaluator.compute_cer(
    hypothesis="कुल राशि ₹125000",
    reference="कुल राशि ₹1,25,000"
)
print(f"CER: {cer:.4f}")

wer = evaluator.compute_wer(
    hypothesis="Total amount 125000",
    reference="Total amount 1,25,000"
)
print(f"WER: {wer:.4f}")
```

## SUPPORTED FEATURES

### Input Formats
- ✅ PNG images
- ✅ JPG/JPEG images
- ✅ GIF images
- ✅ BMP images
- ✅ Document scans (300+ DPI recommended)

### Output Formats
- ✅ JSON (pipeline_results.json)
- ✅ PostgreSQL database
- ✅ Console output
- ✅ Error logs

### Languages Supported
- Hindi (hin)
- Telugu (tel)
- Tamil (tam)
- Bengali (ben)
- Marathi (mar)
- Gujarati (guj)
- Kannada (kan)
- Malayalam (mal)
- Punjabi (pan)
- Urdu (urd)
- English (eng)

### Document Types
- 📄 GST Invoices
- 📊 Bank Statements
- 📋 Annual Reports
- ⚖️ Legal Notices
- 📑 Financial Documents

### Extracted Fields
- company_name
- invoice_number
- invoice_date (YYYY-MM-DD)
- total_amount (float)
- gst_number (GSTIN format)
- bank_account
- transaction_amount
- transaction_date
- document_type

### Accuracy Metrics
- Character Error Rate (CER)
- Word Error Rate (WER)
- Average metrics across dataset
- Per-document metrics

## SYSTEM REQUIREMENTS

### Minimum
- Python 3.8+
- 4GB RAM
- 10GB disk space (models + data)
- CPU: 4 cores

### Recommended
- Python 3.10+
- 16GB RAM
- GPU: NVIDIA with 6GB+ VRAM
- 50GB disk space
- PostgreSQL 13+

## COMMON ISSUES & SOLUTIONS

### GPU Not Available
```python
# Use CPU instead
pipeline = DocumentProcessingPipeline(device='cpu')
```

### Models Not Found
```bash
# Ensure models are in correct location
ls backend/models/indic_trocr/
ls backend/models/indictrans2/

# If not found, clone them
git clone https://github.com/AI4Bharat/IndicTrOCR backend/models/indic_trocr
git clone https://github.com/AI4Bharat/IndicTrans2 backend/models/indictrans2
```

### Database Errors
```bash
# Check PostgreSQL connection
psql -U postgres -d intelli_credit

# Set DATABASE_URL if needed
export DATABASE_URL=postgresql://user:pass@localhost:5432/db
```

### Out of Memory
```python
# Process smaller batches
batch_size = 1  # Process one image at a time
for image in images:
    pipeline.process_document(image)
```

## PERFORMANCE TIPS

1. **GPU Processing**: 2-5x faster than CPU
2. **Batch Size**: Larger = faster (if memory allows)
3. **Image Quality**: Higher DPI = better OCR accuracy
4. **Language**: English typically fastest
5. **Cache Models**: First run loads models (slow), subsequent runs are faster

## API DOCUMENTATION

For detailed API documentation, see: `backend/modules/`

- `ocr_module.py` - OCR extraction
- `translation_module.py` - Machine translation
- `extraction_module.py` - Field extraction
- `database_module.py` - Database operations
- `evaluation_module.py` - Accuracy evaluation
- `pipeline.py` - Pipeline orchestration

## NEXT STEPS

1. ✅ Install models
2. ✅ Add test images
3. ✅ Run pipeline
4. 📊 Review results
5. 🔧 Integrate with your system
6. 📈 Monitor accuracy metrics

## SUPPORT & DOCUMENTATION

- **Setup Guide**: See `SETUP_GUIDE_OCR_PIPELINE.md`
- **GitHub Issues**: https://github.com/AI4Bharat/IndicTrOCR/issues
- **AI4Bharat**: https://ai4bharat.org/
- **Code Comments**: Check docstrings in each module

---

Ready to process your first document? Run:
```bash
cd backend
python pipeline.py
```
