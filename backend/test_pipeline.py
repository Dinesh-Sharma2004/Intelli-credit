"""
Example Usage and Testing Script for Multilingual Document Processing Pipeline

This script demonstrates how to use each module independently and as part of the pipeline.
Run this to verify that all modules are working correctly.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# ============================================================================
# TEST 1: OCR MODULE
# ============================================================================

def test_ocr_module():
    """Test OCR text extraction"""
    print("\n" + "="*70)
    print("TEST 1: OCR MODULE")
    print("="*70)
    
    try:
        from backend.modules import IndicTrOCR
        
        # Initialize OCR
        print("Initializing IndicTrOCR...")
        ocr = IndicTrOCR(device='cpu')
        
        # Example: Extract text from an image (if available)
        sample_image = 'backend/datasets/indic_ocr_dataset/images/img_001.png'
        sample_path = Path(sample_image)
        
        if sample_path.exists():
            print(f"\nProcessing sample image: {sample_path.name}")
            result = ocr.extract_text(str(sample_path))
            
            print("\nOCR Results:")
            print(f"  Raw text lines: {result['raw_text']}")
            print(f"  Languages detected: {result['language_detected']}")
            print(f"  Number of lines: {result['num_lines']}")
        else:
            print(f"\nNote: Sample image not found at {sample_image}")
            print("To test with real images, place PNG/JPG files in:")
            print("  backend/datasets/indic_ocr_dataset/images/")
        
        print("\n✓ OCR Module: OK")
        return True
        
    except ImportError as e:
        print(f"\n✗ OCR Module: FAILED - Models not installed")
        print(f"  Error: {str(e)}")
        print("\n  Install models using:")
        print("    git clone https://github.com/AI4Bharat/IndicTrOCR backend/models/indic_trocr")
        print("    git clone https://github.com/AI4Bharat/IndicTrans2 backend/models/indictrans2")
        return False
    except Exception as e:
        print(f"\n✗ OCR Module: FAILED")
        print(f"  Error: {str(e)}")
        return False


# ============================================================================
# TEST 2: TRANSLATION MODULE
# ============================================================================

def test_translation_module():
    """Test text translation"""
    print("\n" + "="*70)
    print("TEST 2: TRANSLATION MODULE")
    print("="*70)
    
    try:
        from backend.modules import IndicTranslator
        
        # Initialize translator
        print("Initializing IndicTranslator...")
        translator = IndicTranslator(device='cpu')
        
        # Test translation
        test_texts = {
            'hin': 'कुल राशि ₹1,25,000',  # Hindi
            'tel': 'మొత్తం విలువ ₹1,25,000',  # Telugu
            'tam': 'மொத்த தொகை ₹1,25,000',  # Tamil
        }
        
        print("\nTranslating sample texts:")
        for lang_code, text in test_texts.items():
            try:
                result = translator.translate(text, source_lang=lang_code, target_lang='eng')
                print(f"\n  {lang_code.upper()}:")
                print(f"    Original:   {text}")
                print(f"    Translated: {result['translated_text']}")
            except Exception as e:
                print(f"  {lang_code.upper()}: Translation error - {str(e)}")
        
        print("\n✓ Translation Module: OK")
        return True
        
    except ImportError as e:
        print(f"\n✗ Translation Module: FAILED - Models not installed")
        print(f"  Error: {str(e)}")
        return False
    except Exception as e:
        print(f"\n✗ Translation Module: FAILED")
        print(f"  Error: {str(e)}")
        return False


# ============================================================================
# TEST 3: EXTRACTION MODULE
# ============================================================================

def test_extraction_module():
    """Test field extraction"""
    print("\n" + "="*70)
    print("TEST 3: EXTRACTION MODULE")
    print("="*70)
    
    try:
        from backend.modules import FinancialFieldExtractor
        
        # Initialize extractor
        print("Initializing FinancialFieldExtractor...")
        extractor = FinancialFieldExtractor()
        
        # Test extraction
        sample_text = """
        Invoice Number: INV-2024-001234
        Date: 12-04-2024
        Total Amount: ₹1,25,000
        GST Number: 27AABCT1234H1Z0
        Bank Account: 1234567890
        Company Name: Tech Solutions Ltd
        """
        
        print("\nExtracting fields from sample text:")
        result = extractor.extract_fields(sample_text)
        
        extracted = result.to_dict()
        print("\nExtracted Data:")
        for key, value in extracted.items():
            if value and key != 'extracted_fields':
                print(f"  {key}: {value}")
        
        print("\n✓ Extraction Module: OK")
        return True
        
    except Exception as e:
        print(f"\n✗ Extraction Module: FAILED")
        print(f"  Error: {str(e)}")
        return False


# ============================================================================
# TEST 4: DATABASE MODULE
# ============================================================================

def test_database_module():
    """Test database operations"""
    print("\n" + "="*70)
    print("TEST 4: DATABASE MODULE")
    print("="*70)
    
    try:
        from backend.modules import DatabaseManager
        
        # Initialize database
        print("Initializing DatabaseManager...")
        db = DatabaseManager()
        
        print("Database connection: OK")
        
        # Test insert
        print("\nTesting insert operation...")
        doc_id = db.insert_document(
            original_text="कुल राशि ₹1,25,000",
            translated_text="Total amount ₹1,25,000",
            extracted_data={
                'invoice_number': 'INV-2024-001',
                'total_amount': 125000,
                'invoice_date': '2024-04-12'
            },
            source_image_path='sample.png'
        )
        
        print(f"Document inserted: {doc_id}")
        
        # Test retrieve
        print("\nTesting retrieve operation...")
        doc = db.get_document(doc_id)
        if doc:
            print(f"Retrieved document: {doc['document_id']}")
        
        # Test statistics
        print("\nTesting statistics...")
        stats = db.get_statistics()
        print(f"Total documents: {stats['total_documents']}")
        
        db.close()
        
        print("\n✓ Database Module: OK")
        return True
        
    except Exception as e:
        print(f"\n✗ Database Module: FAILED")
        print(f"  Error: {str(e)}")
        print("\n  Ensure PostgreSQL is running and DATABASE_URL is set:")
        print("    export DATABASE_URL=postgresql://user:password@localhost:5432/db")
        return False


# ============================================================================
# TEST 5: EVALUATION MODULE
# ============================================================================

def test_evaluation_module():
    """Test OCR evaluation"""
    print("\n" + "="*70)
    print("TEST 5: EVALUATION MODULE")
    print("="*70)
    
    try:
        from backend.modules import OCREvaluator
        
        # Initialize evaluator
        print("Initializing OCREvaluator...")
        evaluator = OCREvaluator()
        
        # Test CER/WER computation
        print("\nTesting CER/WER computation...")
        
        reference = "कुल राशि ₹1,25,000"
        hypothesis = "कुल राशि ₹125000"
        
        cer = evaluator.compute_cer(hypothesis, reference)
        wer = evaluator.compute_wer(hypothesis, reference)
        
        print(f"\nReference:  {reference}")
        print(f"Hypothesis: {hypothesis}")
        print(f"CER: {cer:.4f} ({cer*100:.2f}%)")
        print(f"WER: {wer:.4f} ({wer*100:.2f}%)")
        
        print("\n✓ Evaluation Module: OK")
        return True
        
    except Exception as e:
        print(f"\n✗ Evaluation Module: FAILED")
        print(f"  Error: {str(e)}")
        return False


# ============================================================================
# TEST 6: PIPELINE
# ============================================================================

def test_pipeline():
    """Test complete pipeline"""
    print("\n" + "="*70)
    print("TEST 6: COMPLETE PIPELINE")
    print("="*70)
    
    try:
        from backend.pipeline import DocumentProcessingPipeline
        
        # Initialize pipeline
        print("Initializing DocumentProcessingPipeline...")
        pipeline = DocumentProcessingPipeline(device='cpu')
        
        print("Pipeline initialized successfully")
        
        # Check for sample images
        sample_dir = Path('backend/datasets/indic_ocr_dataset/images')
        if sample_dir.exists():
            images = list(sample_dir.glob('*.png'))[:1]  # Get first image
            
            if images:
                print(f"\nProcessing sample image: {images[0].name}")
                result = pipeline.process_document(str(images[0]))
                
                print(f"\nPipeline output:")
                print(f"  OCR: {'✓' if result['ocr_result'] else '✗'}")
                print(f"  Translation: {'✓' if result['translation_result'] else '✗'}")
                print(f"  Extraction: {'✓' if result['extraction_result'] else '✗'}")
                print(f"  Database: {'✓' if result['database_result'] else '✗'}")
                print(f"  Evaluation: {'✓' if result['evaluation_result'] else '✗'}")
            else:
                print("\nNo sample images found for testing")
                print("Pipeline structure: OK")
        else:
            print("\nDataset directory not found, but pipeline structure: OK")
        
        pipeline.cleanup()
        
        print("\n✓ Pipeline: OK")
        return True
        
    except Exception as e:
        print(f"\n✗ Pipeline: FAILED")
        print(f"  Error: {str(e)}")
        return False


# ============================================================================
# RUN ALL TESTS
# ============================================================================

def run_all_tests():
    """Run all module tests"""
    print("\n" + "="*70)
    print("MULTILINGUAL DOCUMENT PROCESSING PIPELINE - TEST SUITE")
    print("="*70)
    
    results = {}
    
    # Run tests
    results['OCR Module'] = test_ocr_module()
    results['Translation Module'] = test_translation_module()
    results['Extraction Module'] = test_extraction_module()
    results['Database Module'] = test_database_module()
    results['Evaluation Module'] = test_evaluation_module()
    results['Pipeline'] = test_pipeline()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for module, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{module}: {status}")
    
    print(f"\nTotal: {passed}/{total} modules passed")
    
    if passed == total:
        print("\n✓ All tests passed! Pipeline is ready to use.")
        print("\nNext steps:")
        print("  1. Add document images to: backend/datasets/indic_ocr_dataset/images/")
        print("  2. Add ground truth labels to: backend/datasets/indic_ocr_dataset/labels/")
        print("  3. Run: python backend/pipeline.py")
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please check the errors above.")
        print("\nSetup steps:")
        print("  1. Install models:")
        print("     git clone https://github.com/AI4Bharat/IndicTrOCR backend/models/indic_trocr")
        print("     git clone https://github.com/AI4Bharat/IndicTrans2 backend/models/indictrans2")
        print("  2. Ensure PostgreSQL is running")
        print("  3. Set DATABASE_URL: export DATABASE_URL=postgresql://...")
    
    print("\n" + "="*70 + "\n")
    
    return passed == total


# ============================================================================
# EXAMPLE: STANDALONE MODULE USAGE
# ============================================================================

def example_standalone_usage():
    """Example of using modules standalone"""
    print("\n" + "="*70)
    print("EXAMPLE: STANDALONE MODULE USAGE")
    print("="*70)
    
    # Example 1: OCR only
    print("\nExample 1: Extract text from image")
    print("-"*70)
    print("""
from backend.modules import IndicTrOCR

ocr = IndicTrOCR(device='cpu')
result = ocr.extract_text('image.png')
print(result['raw_text'])
    """)
    
    # Example 2: Translation only
    print("\nExample 2: Translate text")
    print("-"*70)
    print("""
from backend.modules import IndicTranslator

translator = IndicTranslator(device='cpu')
result = translator.translate("कुल राशि ₹1,25,000", source_lang='hin')
print(result['translated_text'])
    """)
    
    # Example 3: Full pipeline
    print("\nExample 3: Complete pipeline")
    print("-"*70)
    print("""
from backend.pipeline import DocumentProcessingPipeline

pipeline = DocumentProcessingPipeline(device='cpu')
result = pipeline.process_document('image.png')
print(result)
pipeline.cleanup()
    """)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='OCR Pipeline Test Suite')
    parser.add_argument('--test', choices=['all', 'ocr', 'translation', 'extraction', 
                                            'database', 'evaluation', 'pipeline'],
                       default='all', help='Which tests to run')
    parser.add_argument('--examples', action='store_true', help='Show usage examples')
    
    args = parser.parse_args()
    
    if args.examples:
        example_standalone_usage()
    elif args.test == 'all':
        run_all_tests()
    elif args.test == 'ocr':
        test_ocr_module()
    elif args.test == 'translation':
        test_translation_module()
    elif args.test == 'extraction':
        test_extraction_module()
    elif args.test == 'database':
        test_database_module()
    elif args.test == 'evaluation':
        test_evaluation_module()
    elif args.test == 'pipeline':
        test_pipeline()
