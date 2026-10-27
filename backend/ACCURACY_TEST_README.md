# OCR Model Accuracy Testing

This directory contains scripts to evaluate the multilingual OCR model's accuracy on the Dataset.

## Quick Start

### Windows
```bash
run_accuracy_test.bat
```

### Linux/Mac
```bash
bash run_accuracy_test.sh
```

## What It Does

The accuracy test performs the following:

1. **Initializes Models**
   - Loads IndicTrOCR for text extraction
   - Loads IndicTrans2 for translation
   - Loads OCREvaluator for metrics computation

2. **Tests Each Language**
   - Assamese
   - Gujarati
   - Hindi
   - Kannada
   - Malayalam
   - Marathi
   - Odia
   - Punjabi
   - Tamil
   - Telugu
   - Urdu

3. **Computes Accuracy Metrics**
   - **CER (Character Error Rate)**: Percentage of character-level differences
   - **WER (Word Error Rate)**: Percentage of word-level differences

4. **Generates Report**
   - Per-language results
   - Overall statistics
   - Saves to `backend/model_accuracy_report.json`

## Output Example

```
============================================================================
OCR MODEL ACCURACY TEST
============================================================================

Testing Language: Hindi (hin)
[1/5] Processing: 0_gt
  ✓ CER: 0.0450 (4.50%)  WER: 0.0800 (8.00%)
[2/5] Processing: 1_gt
  ✓ CER: 0.0320 (3.20%)  WER: 0.0600 (6.00%)

Hindi Summary
──────────────────────────────────────────────────────────────────────────
Documents Tested: 5/5
Average CER: 0.0400 (4.00%)
Average WER: 0.0700 (7.00%)
CER Range: 0.0320 - 0.0450
WER Range: 0.0600 - 0.0800
──────────────────────────────────────────────────────────────────────────

============================================================================
OVERALL ACCURACY SUMMARY
============================================================================

Total Documents Tested: 55
Total Successful: 55

CHARACTER ERROR RATE (CER)
  Average: 0.0420 (4.20%)
  Min: 0.0100
  Max: 0.0850

WORD ERROR RATE (WER)
  Average: 0.0750 (7.50%)
  Min: 0.0300
  Max: 0.1200

Per-Language Results:
──────────────────────────────────────────────────────────────────────────
Assamese        | Tested:  5/ 5 | CER: 0.0500 (5.00%) | WER: 0.0900 (9.00%)
Gujarati        | Tested:  5/ 5 | CER: 0.0380 (3.80%) | WER: 0.0650 (6.50%)
Hindi           | Tested:  5/ 5 | CER: 0.0400 (4.00%) | WER: 0.0700 (7.00%)
Kannada         | Tested:  5/ 5 | CER: 0.0420 (4.20%) | WER: 0.0780 (7.80%)
Malayalam       | Tested:  5/ 5 | CER: 0.0450 (4.50%) | WER: 0.0820 (8.20%)
Marathi         | Tested:  5/ 5 | CER: 0.0390 (3.90%) | WER: 0.0680 (6.80%)
Odia            | Tested:  5/ 5 | CER: 0.0480 (4.80%) | WER: 0.0880 (8.80%)
Punjabi         | Tested:  5/ 5 | CER: 0.0410 (4.10%) | WER: 0.0750 (7.50%)
Tamil           | Tested:  5/ 5 | CER: 0.0430 (4.30%) | WER: 0.0800 (8.00%)
Telugu          | Tested:  5/ 5 | CER: 0.0400 (4.00%) | WER: 0.0710 (7.10%)
Urdu            | Tested:  5/ 5 | CER: 0.0460 (4.60%) | WER: 0.0840 (8.40%)
──────────────────────────────────────────────────────────────────────────

Results saved to: backend/model_accuracy_report.json
```

## Interpreting Results

### CER (Character Error Rate)
- **0-3%**: Excellent (production-ready)
- **3-5%**: Good (acceptable)
- **5-10%**: Fair (needs improvement)
- **>10%**: Poor (requires retraining/optimization)

### WER (Word Error Rate)
- **0-5%**: Excellent
- **5-10%**: Good
- **10-15%**: Fair
- **>15%**: Poor

## Output Files

### model_accuracy_report.json
Contains:
- Timestamp of test
- Device used (CPU/GPU)
- Per-language results
- Per-document metrics
- Overall statistics
- Any errors encountered

Example structure:
```json
{
  "timestamp": "2024-04-12T10:30:45.123456",
  "device": "cpu",
  "models_initialized": {
    "ocr": true,
    "translator": true,
    "evaluator": true
  },
  "language_results": {
    "hindi": {
      "language": "Hindi",
      "language_code": "hin",
      "images_tested": 5,
      "successful": 5,
      "average_cer": 0.0400,
      "average_wer": 0.0700,
      "document_results": [...]
    }
  },
  "overall_metrics": {
    "total_documents_tested": 55,
    "average_cer": 0.0420,
    "average_wer": 0.0750
  }
}
```

## Customizing the Test

### Modify Maximum Images Per Language

Edit `backend/test_accuracy.py` and change the test:

```python
# Test first 10 images per language
tester.run_all_languages(max_images_per_language=10)
```

### Test Single Language

```python
from backend.test_accuracy import ModelAccuracyTester
from pathlib import Path

tester = ModelAccuracyTester(device='cpu')
dataset_root = Path(__file__).parent / 'Dataset' / 'verified_twice'

result = tester.test_language(
    'hin',
    'Hindi',
    dataset_root / 'hindi',
    max_images=5
)

print(result)
```

### Use GPU

```bash
# Modify test script to use GPU
device='cuda'
```

## Troubleshooting

### No Virtual Environment
```bash
# Windows
setup-windows.bat

# Linux/Mac
bash setup-linux.sh
```

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

### OutOfMemory Error
```python
# Use CPU with single image at a time
device='cpu'
# Or reduce max_images_per_language
max_images_per_language=1
```

## Related Documentation

- [VENV_QUICKSTART.md](../VENV_QUICKSTART.md) - Quick start guide
- [SETUP_GUIDE_OCR_PIPELINE.md](../SETUP_GUIDE_OCR_PIPELINE.md) - Detailed setup
- [OCR_PIPELINE_README.md](../OCR_PIPELINE_README.md) - Complete documentation

## Performance Metrics

### Expected Accuracy Ranges (without fine-tuning)
- **Hindi**: 3-5% CER, 6-8% WER
- **Tamil**: 4-6% CER, 7-10% WER
- **Telugu**: 3-5% CER, 6-8% WER
- **Gujarati**: 3-5% CER, 6-8% WER
- **Kannada**: 4-6% CER, 8-10% WER
- **Malayalam**: 4-6% CER, 8-10% WER
- **Marathi**: 3-5% CER, 6-8% WER
- **Punjabi**: 4-6% CER, 7-9% WER
- **Urdu**: 5-7% CER, 9-11% WER
- **Assamese**: 5-7% CER, 9-11% WER
- **Odia**: 4-6% CER, 8-10% WER

(These are approximate values - actual results depend on document quality and training data)

## Support

For issues or questions:
1. Check model initialization logs in output
2. Verify Dataset structure at `backend/Dataset/verified_twice/`
3. Ensure all models are properly installed
4. Check `model_accuracy_report.json` for detailed error information
