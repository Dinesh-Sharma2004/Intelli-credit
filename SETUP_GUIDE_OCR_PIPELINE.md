"""
Setup Guide for Multilingual Document Processing Pipeline

This guide provides step-by-step instructions to set up and run the
document processing pipeline for Indian financial documents.
"""

# ============================================================================
# INSTALLATION AND SETUP GUIDE
# ============================================================================

## 1. ENVIRONMENT SETUP

### 1.1 Using Existing Virtual Environment

If a virtual environment already exists:

#### Windows
```bash
# Quick activation
activate.bat
```

#### Linux/Mac
```bash
# Quick activation
source activate.sh
```

### 1.2 Create Python Virtual Environment (if not exists)

#### Windows
```bash
# Automatic setup with dependencies
setup-windows.bat
```

#### Linux/Mac
```bash
# Automatic setup with dependencies
bash setup-linux.sh
```

#### Manual Setup
```bash
# On Windows
python -m venv venv
venv\Scripts\activate.bat

# On Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 1.2 Install Dependencies

After virtual environment is activated:

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

## 2. MODEL INSTALLATION

The pipeline uses two AI models from AI4Bharat that must be cloned locally:

### 2.1 Install IndicTrOCR (Optical Character Recognition)
```bash
git clone https://github.com/AI4Bharat/IndicTrOCR backend/models/indic_trocr
cd backend/models/indic_trocr
pip install -e .
cd ../../..
```

**What it does:** Extracts multilingual text from document images
**Supported Languages:** Hindi, Telugu, Tamil, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Urdu, English

### 2.2 Install IndicTrans2 (Machine Translation)
```bash
git clone https://github.com/AI4Bharat/IndicTrans2 backend/models/indictrans2
cd backend/models/indictrans2
pip install -e .
cd ../../..
```

**What it does:** Translates Indian language text to English
**Supported Language Pairs:** All Indian languages to English

## 3. DATABASE SETUP

### 3.1 PostgreSQL Installation

#### On Windows
```bash
# Using Installer
# Download from https://www.postgresql.org/download/windows/

# Or using Chocolatey
choco install postgresql
```

#### On Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

#### On Mac
```bash
brew install postgresql
brew services start postgresql
```

### 3.2 Create Database and User

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE intelli_credit;

# Create user (optional)
CREATE USER intelli_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE intelli_credit TO intelli_user;

# Verify
\l  # List databases
\q  # Quit
```

### 3.3 Configure Database Connection

Create a `.env` file in the backend directory:

```bash
# backend/.env
DATABASE_URL=postgresql://intelli_user:secure_password@localhost:5432/intelli_credit
```

Or set environment variable:
```bash
export DATABASE_URL=postgresql://intelli_user:secure_password@localhost:5432/intelli_credit
```

## 4. DATASET PREPARATION

### 4.1 Existing Dataset Structure

The dataset is already available in the project:

```
backend/
├── Dataset/
│   └── verified_twice/
│       ├── assamese/
│       ├── gujarati/
│       ├── hindi/
│       ├── kannada/
│       ├── malayalam/
│       ├── marathi/
│       ├── odia/
│       ├── punjabi/
│       ├── tamil/
│       ├── telugu/
│       └── urdu/
```

Each language directory contains ground truth text files (*.txt):
- `img_001.txt` - Ground truth for img_001.png
- `img_002.txt` - Ground truth for img_002.png
- etc.

### 4.2 Ground Truth Label Format

Each `.txt` file contains the exact text that appears in the corresponding image.

Example: `hindi/0_gt.txt`
```
कुल राशि ₹1,25,000
तारीख 12-04-2024
जीएसटी संख्या: 27AABCT1234H1Z0
```

## 5. RUNNING THE PIPELINE

### 5.1 Basic Usage

```python
from backend.pipeline import DocumentProcessingPipeline

# Initialize pipeline
pipeline = DocumentProcessingPipeline(device='cuda')  # or 'cpu'

# Process a single document
result = pipeline.process_document('path/to/image.png')

# Process multiple documents
batch_results = pipeline.process_batch([
    'path/to/img1.png',
    'path/to/img2.png'
])

# Process entire dataset
dataset_results = pipeline.process_dataset()

# Get statistics
stats = pipeline.get_statistics()

# Save results
pipeline.save_results('pipeline_results.json')

# Cleanup
pipeline.cleanup()
```

### 5.2 Command Line Usage

```bash
# From backend directory
python pipeline.py
```

### 5.3 Processing Flow

For each document:

1. **OCR Extraction** (IndicTrOCR)
   - Input: Document image
   - Output: Extracted text in original language
   - Supported: Indian scripts (Devanagari, Tamil, Telugu, etc.)

2. **Text Translation** (IndicTrans2)
   - Input: Extracted text
   - Output: English translation
   - Quality: High accuracy for Indian languages

3. **Field Extraction**
   - Extracts structured data:
     - Invoice number
     - Invoice date
     - Total amount
     - GST number
     - Bank account number
     - Company name
     - Document type

4. **Database Storage** (PostgreSQL)
   - Stores:
     - Original OCR text
     - Translated English text
     - Extracted structured fields
     - Processing metadata

5. **Accuracy Evaluation**
   - Computes CER (Character Error Rate)
   - Computes WER (Word Error Rate)
   - Compares against ground truth labels

## 6. PYTHON API REFERENCE

### 6.1 IndicTrOCR Module

```python
from backend.modules import IndicTrOCR

# Initialize OCR
ocr = IndicTrOCR(device='cuda')

# Extract text from image
result = ocr.extract_text('path/to/image.png')

# Returns:
# {
#     "image_path": "...",
#     "raw_text": ["line1", "line2", ...],
#     "full_text": "combined text",
#     "language_detected": ["hin", "eng"],
#     "num_lines": 5
# }

# Batch processing
results = ocr.extract_text_batch(['img1.png', 'img2.png'])
```

### 6.2 IndicTranslator Module

```python
from backend.modules import IndicTranslator

# Initialize translator
translator = IndicTranslator(device='cuda')

# Translate text
result = translator.translate(
    text="कुल राशि ₹1,25,000",
    source_lang='hin',
    target_lang='eng'
)

# Returns:
# {
#     "original_text": "कुल राशि ₹1,25,000",
#     "translated_text": "Total amount ₹1,25,000",
#     "source_language": "Hindi",
#     "target_language": "English"
# }

# Auto-detect and translate
result = translator.detect_and_translate(
    text="कुल राशि ₹1,25,000",
    target_lang='eng'
)

# Batch translation
results = translator.translate_batch(texts=['text1', 'text2'])
```

### 6.3 FinancialFieldExtractor Module

```python
from backend.modules import FinancialFieldExtractor

# Initialize extractor
extractor = FinancialFieldExtractor()

# Extract fields
result = extractor.extract_fields(
    "Invoice Number: INV-2024-001\n"
    "Date: 12-04-2024\n"
    "Total Amount: ₹1,25,000\n"
    "GSTIN: 27AABCT1234H1Z0"
)

# Returns FinancialExtraction object with:
# - invoice_number
# - invoice_date
# - total_amount
# - gst_number
# - bank_account
# - And more...
```

### 6.4 DatabaseManager Module

```python
from backend.modules import DatabaseManager

# Initialize database
db = DatabaseManager(database_url='postgresql://user:pass@localhost:5432/db')

# Insert document
document_id = db.insert_document(
    original_text="कुल राशि ₹1,25,000",
    translated_text="Total amount ₹1,25,000",
    extracted_data={'invoice_number': 'INV-001'},
    source_image_path='path/to/image.png'
)

# Query documents
doc = db.get_document(document_id)
all_docs = db.get_all_documents(limit=10)

# Search documents
results = db.search_documents(gst_number='27AABCT1234H1Z0')

# Update document
updated = db.update_document(document_id, total_amount=150000)

# Get statistics
stats = db.get_statistics()
```

### 6.5 OCREvaluator Module

```python
from backend.modules import OCREvaluator

# Initialize evaluator
evaluator = OCREvaluator()

# Load ground truth
ground_truth = evaluator.load_ground_truth('img_001.png')

# Compute metrics
cer = evaluator.compute_cer(
    hypothesis="कुल राशि ₹125000",
    reference="कुल राशि ₹1,25,000"
)

wer = evaluator.compute_wer(
    hypothesis="कुल राशि ₹125000",
    reference="कुल राशि ₹1,25,000"
)

# Evaluate single document
result = evaluator.evaluate_single_document('img_001.png', 'detected_text')

# Evaluate entire dataset
summary = evaluator.evaluate_dataset(ocr_results={
    'img_001.png': 'detected_text1',
    'img_002.png': 'detected_text2'
})
```

## 7. SUPPORTED LANGUAGES AND SCRIPTS

### Indian Languages
- **Hindi** (hin) - Devanagari script
- **Telugu** (tel) - Telugu script
- **Tamil** (tam) - Tamil script
- **Bengali** (ben) - Bengali script
- **Marathi** (mar) - Devanagari script
- **Gujarati** (guj) - Gujarati script
- **Kannada** (kan) - Kannada script
- **Malayalam** (mal) - Malayalam script
- **Punjabi** (pan) - Gurmukhi script
- **Urdu** (urd) - Arabic/Persian script

### English
- **English** (eng) - Latin script

## 8. CONFIGURATION OPTIONS

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/intelli_credit

# Model paths (optional - uses defaults if not set)
INDIC_TROCR_PATH=/path/to/model
INDICTRANS2_PATH=/path/to/model

# GPU configuration
CUDA_VISIBLE_DEVICES=0  # GPU device ID
```

### Pipeline Configuration

```python
pipeline = DocumentProcessingPipeline(
    ocr_model_path='/custom/path/to/trocr',
    translation_model_path='/custom/path/to/trans2',
    dataset_path='/custom/path/to/dataset',
    database_url='postgresql://...',
    device='cuda'  # or 'cpu'
)
```

## 9. TROUBLESHOOTING

### Issue: Model Loading Fails

**Solution:**
```bash
# Ensure models are cloned correctly
git clone https://github.com/AI4Bharat/IndicTrOCR backend/models/indic_trocr
git clone https://github.com/AI4Bharat/IndicTrans2 backend/models/indictrans2

# Verify installation
ls backend/models/indic_trocr/
ls backend/models/indictrans2/
```

### Issue: CUDA Out of Memory

**Solution:**
```python
# Use CPU instead
pipeline = DocumentProcessingPipeline(device='cpu')

# Or reduce batch size
batch_results = pipeline.process_batch(image_paths[:1])
```

### Issue: Database Connection Failed

**Solution:**
```bash
# Verify PostgreSQL is running
psql -U postgres -d intelli_credit

# Check DATABASE_URL in .env
echo $DATABASE_URL

# Reset connection
db = DatabaseManager()  # Will reinitialize
```

### Issue: No Ground Truth Labels

**Solution:**
```bash
# Create label files manually
echo "कुल राशि ₹1,25,000" > backend/datasets/indic_ocr_dataset/labels/img_001.txt
```

## 10. PERFORMANCE OPTIMIZATION

### For CPU Processing
```python
pipeline = DocumentProcessingPipeline(device='cpu')
```

### For GPU Processing
```python
import torch

# Check GPU availability
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))

# Use GPU
pipeline = DocumentProcessingPipeline(device='cuda')
```

### Batch Processing
```python
# Process in smaller batches for memory efficiency
batch_size = 5
for i in range(0, len(image_list), batch_size):
    batch = image_list[i:i+batch_size]
    results = pipeline.process_batch(batch)
```

## 11. OUTPUT FILES

### Results JSON Structure

```json
{
  "pipeline_statistics": {
    "total_documents_processed": 5,
    "total_errors": 0,
    "processing_timestamp": "2024-04-12T10:30:45.123456",
    "database_stats": {...},
    "ocr_metrics": {
      "average_cer": 0.04,
      "average_wer": 0.08
    }
  },
  "documents": [
    {
      "image_path": "...",
      "timestamp": "...",
      "ocr_result": {...},
      "translation_result": {...},
      "extraction_result": {...},
      "database_result": {...},
      "evaluation_result": {...}
    }
  ],
  "errors": []
}
```

## 12. NEXT STEPS

1. Install models: Clone IndicTrOCR and IndicTrans2
2. Set up PostgreSQL database
3. Prepare dataset with images and ground truth labels
4. Run `python pipeline.py` to test
5. Integrate into production system

For more information, visit:
- IndicTrOCR: https://github.com/AI4Bharat/IndicTrOCR
- IndicTrans2: https://github.com/AI4Bharat/IndicTrans2
- AI4Bharat: https://ai4bharat.org/
