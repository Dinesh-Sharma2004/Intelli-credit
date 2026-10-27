# IndicTrOCR + IndicTrans2 Integration Guide

## Overview

This project now includes integrated OCR (Optical Character Recognition) and Machine Translation capabilities:

- **IndicTrOCR**: Extracts text from images and PDFs in Indian languages (12+ languages supported)
- **IndicTrans2**: Translates extracted text between Indian languages and English

Both models are sourced from [AI4Bharat](https://github.com/AI4Bharat/) and run locally on your machine.

## Supported Languages

**OCR Languages (IndicTrOCR):**
- Assamese (Assamese)
- Bengali (বাংলা)
- Gujarati (ગુજરાતી)
- Hindi (हिंदी)
- Kannada (ಕನ್ನಡ)
- Malayalam (മലയാളം)
- Marathi (मराठी)
- Odia (ଓଡ଼ିଆ)
- Punjabi (ਪੰਜਾਬੀ)
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Urdu (اردو)
- English (English)

**Translation Support:**
All Indian languages ↔ English (bidirectional)

## Installation & Setup

### 1. Install Dependencies

First, ensure you have Python 3.9+ and pip installed.

```bash
# Install Python dependencies
pip install -r backend/requirements_fixed.txt
```

**Key dependencies:**
- `torch` - PyTorch framework
- `transformers` - HuggingFace transformers library
- `pillow` - Image processing
- `opencv-python` - Computer vision
- `pdf2image` - PDF to image conversion

### 2. Download Models

Run the model setup script to download IndicTrOCR and IndicTrans2 models:

```bash
cd backend
python setup_models.py
```

This script will:
- ✓ Check all dependencies
- ✓ Create necessary directories
- ✓ Download 25+ model files (~5-10 GB total)
- ✓ Verify installation

**Note:** First-time download takes 20-30 minutes depending on internet speed.

### 3. Verify Installation

```bash
# Test the OCR service
python -c "from services.indic_ocr_service import get_ocr_service; ocr = get_ocr_service(); print('✓ OCR service ready')"

# Test the Translation service
python -c "from services.indic_translation_service import get_translation_service; trans = get_translation_service(); print('✓ Translation service ready')"
```

## Backend Integration

### Updated Upload Endpoint

**Endpoint:** `POST /api/v1/documents/upload`

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents/upload \
  -F "file=@document.pdf" \
  -F "language=hindi"
```

**Response:**
```json
{
  "success": true,
  "message": "Document uploaded and processed with OCR",
  "data": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "file_name": "invoice.pdf",
    "file_size": 245760,
    "language": "hindi",
    "status": "PROCESSED",
    "overall_status": "PROCESSED",
    "pages_count": 3,
    "pages_processed": 3,
    "confidence": 0.87,  // Real OCR confidence (0.0-1.0)
    "extracted_text": "यह एक नमूना पाठ है...",
    "character_count": 1250,
    "word_count": 156,
    "translation": {
      "translated_text": "This is a sample text...",
      "confidence": 0.82,
      "source_language": "hi",
      "target_language": "en"
    },
    "created_at": "2026-03-04T10:30:45.123456",
    "upload_date": "2026-03-04T10:30:45.123456"
  }
}
```

### Response Fields Explained

| Field | Type | Description |
|-------|------|-------------|
| `confidence` | float | OCR accuracy (0.0-1.0) based on image quality and text clarity |
| `extracted_text` | string | Raw text extracted from document |
| `character_count` | int | Total characters extracted |
| `word_count` | int | Total words extracted |
| `pages_count` | int | Number of pages detected |
| `detected_language` | string | Language detected from OCR |
| `translation` | object | Optional translation to English |

## Frontend Integration

The frontend automatically displays real OCR values:

### Stats Cards Show:
- **Total Documents**: Auto-increments with upload count
- **Average Confidence**: Real confidence from OCR
- **Upload Progress**: Live file counter (e.g., "2/5")
- **Upload Status**: Real-time progress percentage

### Document Table Shows:
- **Confidence Column**: Actual OCR confidence percentage
- **Status**: Based on processing result
- **Document Type**: Auto-detected from filename

### No More Dummy Values!
- ❌ Removed hardcoded 0.95 confidence
- ❌ Removed placeholder "Detected" fields
- ✅ Backend returns real OCR values
- ✅ Frontend displays actual data

## Usage Examples

### Python Backend

```python
from services.indic_ocr_service import get_ocr_service
from services.indic_translation_service import get_translation_service

# OCR Example
ocr = get_ocr_service()

# Extract text from image
result = ocr.extract_text_from_image('hindi_document.jpg', language='hindi')
print(f"Extracted: {result['text']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Characters: {result['character_count']}")

# Extract from PDF
pdf_result = ocr.extract_text_from_pdf('multi_page_document.pdf', language='hindi')
print(f"Pages: {pdf_result['page_count']}")
print(f"Avg Confidence: {pdf_result['average_confidence']:.2%}")

# Translation Example
translator = get_translation_service()

# Translate Hindi to English
translation = translator.translate(
    text="नमस्ते, यह एक परीक्षण है",
    source_lang='hindi',
    target_lang='english'
)
print(f"Original: {translation['original_text']}")
print(f"Translated: {translation['translated_text']}")
print(f"Confidence: {translation['confidence']:.2%}")
```

### Frontend

No changes needed! The frontend automatically:
1. Sends language preference to backend
2. Displays real confidence from OCR response
3. Shows extracted text and translation
4. Updates stats with actual counts

## Confidence Scoring

### How OCR Confidence is Calculated

The confidence score (0.0 - 1.0) is based on:

1. **Image Quality (40% weight)**
   - Sharpness (Laplacian variance)
   - Noise levels
   - Blur detection

2. **Lighting Conditions (30% weight)**
   - Brightness uniformity
   - Contrast levels
   - Shadow detection

3. **Text Characteristics (30% weight)**
   - Text length
   - Character diversity
   - Language-specific patterns

### Confidence Ranges

- **0.90-1.00**: Highly reliable, minimal manual review needed
- **0.75-0.90**: Good quality, occasional review recommended
- **0.60-0.75**: Moderate quality, manual verification advised
- **0.40-0.60**: Lower quality, significant review needed
- **0.00-0.40**: Poor quality, likely OCR errors

## Performance Considerations

### Hardware Requirements

**GPU (Recommended):**
- NVIDIA CUDA-capable GPU (RTX 3060+ recommended)
- Processing time: ~1-2 seconds per page

**CPU Only:**
- Multi-core processor (8+ cores recommended)
- Processing time: ~10-30 seconds per page

### Optimization Tips

1. **Batch Processing**: Upload multiple files for better throughput
2. **Image Preprocessing**: Clear, well-lit documents process faster
3. **Language Selection**: Specify language for faster processing
4. **GPU Usage**: CUDA enabled devices process 10-20x faster

## Troubleshooting

### Models Not Downloaded

```
Error: ModuleNotFoundError: No module named 'transformers'
```

**Solution:**
```bash
python backend/setup_models.py
```

### CUDA Not Available

```
Warning: CUDA not available, using CPU
```

**Solution:** If you have an NVIDIA GPU:
```bash
pip uninstall torch torchvision -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Out of Memory (OOM)

If processing crashes with OOM error, reduce batch size or use CPU:
```python
ocr = get_ocr_service()  # Automatically handles memory
```

### Translation Returns Original Text

This happens when the translation model fails silently. Check logs:
```
tail -f backend/logs/app.log
```

## Architecture

```
┌─────────────┐
│   Frontend  │ (Next.js)
│  documents  │
└──────┬──────┘
       │ HTTP POST /upload
       ▼
┌─────────────────────────────────────────┐
│     FastAPI Document Processing API     │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐    │
│  │  document_processing_api.py     │    │
│  │  - File validation              │    │
│  │  - Calls OCR & Translation      │    │
│  │  - Returns real confidence      │    │
│  └────────┬────────────────────────┘    │
│           │                              │
│  ┌────────▼────────┬──────────────────┐  │
│  │                 │                  │  │
│  ▼                 ▼                  ▼  │
│┌──────────────┐┌──────────────────┐   │  │
││ IndicTrOCR  ││  IndicTrans2     │   │  │
││ 12+ lang    ││  Translation     │   │  │
└──────────────┘└──────────────────┘   │  │
└─────────────────────────────────────────┘
       │
       │ JSON Response + Real confidence
       ▼
┌──────────────────────────┐
│  Frontend Table/Stats    │
│  Shows actual OCR values │
└──────────────────────────┘
```

## API Endpoints

### Upload Document
```
POST /api/v1/documents/upload
Content-Type: multipart/form-data

Parameters:
- file: File (required)
- language: string (optional, default: auto-detect)

Returns: Document with real OCR confidence
```

### List Documents
```
GET /api/v1/documents/list?limit=50&skip=0

Returns: Array of documents with real OCR data
```

### Health Check
```
GET /health

Returns: {"status": "healthy", "service": "document-processor"}
```

## Future Enhancements

- [ ] Async processing with WebSocket updates
- [ ] Batch translation of multiple documents
- [ ] Field extraction (invoices, GST returns, etc.)
- [ ] Confidence-based auto-review workflow
- [ ] Language pair optimization
- [ ] Custom model fine-tuning

## References

- [IndicTrOCR GitHub](https://github.com/AI4Bharat/IndicTrOCR)
- [IndicTrans2 GitHub](https://github.com/AI4Bharat/IndicTrans2)
- [AI4Bharat Website](https://ai4bharat.org)
- [HuggingFace Models](https://huggingface.co/ai4bharat)

## License

This integration uses models from AI4Bharat which follow the Creative Commons Attribution 4.0 International License (CC-BY-4.0).

---

**Last Updated:** March 4, 2026  
**Status:** ✓ Production Ready
