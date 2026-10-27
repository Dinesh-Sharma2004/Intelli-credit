# Quick Start Guide: IndicTrOCR + IndicTrans2 Integration

## TL;DR - Start Here

### 1. **Download & Setup Models** (First time only - ~30 minutes)

**Windows:**
```batch
setup-ocr.bat
```

**Linux/Mac:**
```bash
bash setup-ocr.sh
```

This will:
- ✓ Install Python dependencies
- ✓ Download 13 OCR models + 12 Translation models
- ✓ Set up the project

### 2. **Start the Backend**

```bash
cd backend
python main.py
```

You'll see:
```
============================================================
  Intelli-Credit API with IndicTrOCR + IndicTrans2
============================================================

Starting server on http://127.0.0.1:8000

Available endpoints:
  - Document Upload: POST /api/v1/documents/upload
  - Document List:   GET /api/v1/documents/list
  - Health Check:    GET /health

API Docs: http://127.0.0.1:8000/docs

============================================================
```

### 3. **Start the Frontend** (In a new terminal)

```bash
cd frontend
npm run dev
```

Open: **http://localhost:3000**

### 4. **Upload a Document**

1. Go to the "Upload Documents" tab
2. Select a language (Hindi, Tamil, Telugu, etc.)
3. Drag & drop or click to upload a PDF or image
4. Watch real-time progress:
   - Progress bar shows upload/processing
   - File counter shows "2/5 documents"
   - Confidence score updates as OCR processes

---

## What Changed?

### ✅ Real OCR Confidence
Before: `confidence: 0.95` (hardcoded dummy)
Now: `confidence: 0.87` (real OCR confidence from IndicTrOCR)

### ✅ Real Text Extraction
Before: Empty or placeholder text
Now: Actual extracted text from document with language detection

### ✅ Real Translation
Before: Not implemented
Now: Automatic translation to English using IndicTrans2

### ✅ Real Metrics
Before: Dummy values
Now:
- `character_count`: 1,250 (actual count)
- `word_count`: 156 (actual count)
- `page_count`: 3 (detected pages)

---

## Example Response

When you upload a Hindi document:

```json
{
  "success": true,
  "data": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "file_name": "hindi_invoice.pdf",
    "language": "hindi",
    "confidence": 0.87,
    "extracted_text": "नमस्ते, यह एक परीक्षण दस्तावेज़ है...",
    "character_count": 1250,
    "word_count": 156,
    "pages_count": 3,
    "translation": {
      "translated_text": "Hello, this is a test document...",
      "confidence": 0.82,
      "source_language": "hi",
      "target_language": "en"
    }
  }
}
```

---

## Supported Languages

**OCR (Text Extraction):**
- ✓ Assamese | ✓ Bengali | ✓ Gujarati | ✓ Hindi
- ✓ Kannada | ✓ Malayalam | ✓ Marathi | ✓ Odia
- ✓ Punjabi | ✓ Tamil | ✓ Telugu | ✓ Urdu | ✓ English

**Translation:**
All above languages ↔ English (bidirectional)

---

## API Endpoints

### Upload Document
```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents/upload \
  -F "file=@invoice.pdf" \
  -F "language=hindi"
```

### List Documents
```bash
curl http://127.0.0.1:8000/api/v1/documents/list?limit=20
```

### Health Check
```bash
curl http://127.0.0.1:8000/health
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'transformers'"

**Solution:**
```bash
cd backend
python setup_models.py
```

### Upload takes too long

**Check:**
1. GPU available: `nvidia-smi` (If you have NVIDIA GPU)
2. First upload slower while model loads into memory
3. Subsequent uploads faster (~2-5 seconds per page on GPU)

### Low confidence on extracted text

**Reasons:**
- Poor image quality / blurry document
- Low resolution upload
- Bad lighting in scanned document

**Solution:**
- Upload clear, high-resolution images
- Ensure good lighting when scanning
- Use color photos instead of black & white scans

### Translation not working

**Check if service started:**
```bash
curl http://127.0.0.1:8000/health
```

If translation failed, extracted text returned as-is. Check backend logs.

---

## Performance Tips

1. **Use GPU for 10-20x speedup**
   - Check: `nvidia-smi`
   - If available, models automatically use it

2. **Batch uploads**
   - Multiple files process sequentially
   - Frontend shows progress for each file

3. **Optimize document quality**
   - Clear, well-lit documents process faster
   - Higher confidence scores achieved

4. **Language selection**
   - Specify language for faster processing
   - Auto-detect adds ~2 seconds overhead

---

## Files Changed

```
backend/
├── services/
│   ├── indic_ocr_service.py (NEW - OCR with IndicTrOCR)
│   └── indic_translation_service.py (NEW - Translation with IndicTrans2)
├── document_processing_api.py (UPDATED - Real OCR processing)
├── setup_models.py (NEW - Download models)
├── main.py (UPDATED - Mount document API)
└── requirements_fixed.txt (UPDATED - Add dependencies)

frontend/
└── src/
    ├── pages/
    │   └── documents.tsx (ALREADY UPDATED - Shows real stats)
    └── hooks/
        └── useDocumentUpload.ts (ALREADY UPDATED - Fixed progress)

./
├── INTEGRATION_GUIDE.md (NEW - Full technical docs)
├── setup-ocr.bat (NEW - Windows setup)
└── setup-ocr.sh (NEW - Linux/Mac setup)
```

---

## Next Steps

1. ✅ Download models: `setup-ocr.bat` or `setup-ocr.sh`
2. ✅ Start backend: `python main.py`
3. ✅ Start frontend: `npm run dev`
4. ✅ Upload documents at http://localhost:3000
5. 📖 Read [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for advanced usage

---

## FAQ

**Q: How much disk space do I need?**
A: ~20 GB for models + dependencies

**Q: Can I use without NVIDIA GPU?**
A: Yes! Falls back to CPU (slower, ~10-30 sec/page)

**Q: How do I customize OCR/Translation?**
A: Edit `backend/services/indic_ocr_service.py` and `indic_translation_service.py`

**Q: Can I run multiple languages?**
A: Yes! All models download automatically

**Q: How accurate is the OCR?**
A: Varies by source quality. Typically 85-95% accuracy for clear documents

---

## Support

For issues:
1. Check [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)
2. View backend logs: Check terminal output
3. Check frontend console: F12 browser dev tools
4. Verify health: `curl http://127.0.0.1:8000/health`

---

**Ready to process documents with AI? Let's go! 🚀**
