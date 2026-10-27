"""
Main Pipeline for Multilingual Document Processing

This pipeline orchestrates the complete workflow:
1. Load dataset images
2. Run OCR using IndicTrOCR
3. Display detected text
4. Translate text using IndicTrans2
5. Extract structured financial fields
6. Store results in PostgreSQL database
7. Compute OCR accuracy metrics using ground truth labels
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

# Add backend to Python path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))

from modules import (
    IndicTrOCR,
    IndicTranslator,
    FinancialFieldExtractor,
    DatabaseManager,
    OCREvaluator
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentProcessingPipeline:
    """
    Complete multilingual document processing pipeline.
    
    Processes Indian financial documents through:
    - OCR (Optical Character Recognition)
    - Translation
    - Field Extraction
    - Database Storage
    - Accuracy Evaluation
    """
    
    def __init__(
        self,
        ocr_model_path: Optional[str] = None,
        translation_model_path: Optional[str] = None,
        dataset_path: Optional[str] = None,
        database_url: Optional[str] = None,
        device: str = 'cuda'
    ):
        """
        Initialize the document processing pipeline.
        
        Args:
            ocr_model_path: Path to IndicTrOCR model
            translation_model_path: Path to IndicTrans2 model
            dataset_path: Path to OCR evaluation dataset
            database_url: PostgreSQL connection string
            device: Device to run models on ('cuda' or 'cpu')
        """
        logger.info("Initializing Document Processing Pipeline")
        
        self.device = device
        self.results = {
            'processed_documents': [],
            'errors': [],
            'statistics': {}
        }
        
        # Initialize components
        try:
            logger.info("Loading OCR module...")
            self.ocr = IndicTrOCR(model_path=ocr_model_path, device=device)
        except Exception as e:
            logger.error(f"Failed to initialize OCR: {str(e)}")
            self.ocr = None
        
        try:
            logger.info("Loading Translation module...")
            self.translator = IndicTranslator(
                model_path=translation_model_path,
                device=device
            )
        except Exception as e:
            logger.error(f"Failed to initialize Translator: {str(e)}")
            self.translator = None
        
        try:
            logger.info("Loading Extraction module...")
            self.extractor = FinancialFieldExtractor()
        except Exception as e:
            logger.error(f"Failed to initialize Extractor: {str(e)}")
            self.extractor = None
        
        try:
            logger.info("Initializing Database...")
            self.db = DatabaseManager(database_url=database_url)
        except Exception as e:
            logger.warning(f"Database initialization failed: {str(e)}")
            logger.warning("Continuing without database support")
            self.db = None
        
        try:
            logger.info("Initializing Evaluator...")
            self.evaluator = OCREvaluator(dataset_path=dataset_path)
        except Exception as e:
            logger.warning(f"Evaluator initialization failed: {str(e)}")
            self.evaluator = None
    
    def process_document(
        self,
        image_path: str,
        source_language: str = 'hin',
        target_language: str = 'eng'
    ) -> Dict[str, Any]:
        """
        Process a single document through the complete pipeline.
        
        Args:
            image_path: Path to input image
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing document: {Path(image_path).name}")
        logger.info(f"{'='*70}\n")
        
        result = {
            'image_path': image_path,
            'timestamp': datetime.now().isoformat(),
            'ocr_result': None,
            'translation_result': None,
            'extraction_result': None,
            'database_result': None,
            'evaluation_result': None,
            'errors': []
        }
        
        try:
            # Step 1: OCR
            if self.ocr:
                logger.info("Step 1: Running OCR...")
                ocr_result = self.ocr.extract_text(image_path)
                result['ocr_result'] = ocr_result
            else:
                result['errors'].append("OCR module not available")
                logger.warning("OCR module not available")
            
            # Step 2: Translation
            if self.translator and result['ocr_result']:
                logger.info("Step 2: Translating detected text...")
                
                raw_text = ' '.join(result['ocr_result']['raw_text'])
                
                # Detect language from OCR result
                detected_langs = result['ocr_result'].get('language_detected', [source_language])
                source_lang = detected_langs[0] if detected_langs else source_language
                
                translation_result = self.translator.translate(
                    raw_text,
                    source_lang=source_lang,
                    target_lang=target_language
                )
                result['translation_result'] = translation_result
            else:
                result['errors'].append("Translation not available")
                logger.warning("Translation module not available")
            
            # Step 3: Field Extraction
            if self.extractor:
                logger.info("Step 3: Extracting structured fields...")
                
                # Use translated text for extraction if available
                text_to_extract = result['translation_result']['translated_text'] \
                    if result['translation_result'] else \
                    ' '.join(result['ocr_result']['raw_text']) if result['ocr_result'] else ""
                
                extraction_result = self.extractor.extract_fields(text_to_extract)
                result['extraction_result'] = extraction_result.to_dict()
            else:
                result['errors'].append("Extraction module not available")
                logger.warning("Extraction module not available")
            
            # Step 4: Database Storage
            if self.db and result['extraction_result']:
                logger.info("Step 4: Storing results in database...")
                
                original_text = ' '.join(result['ocr_result']['raw_text']) \
                    if result['ocr_result'] else ""
                translated_text = result['translation_result']['translated_text'] \
                    if result['translation_result'] else ""
                
                try:
                    document_id = self.db.insert_document(
                        original_text=original_text,
                        translated_text=translated_text,
                        extracted_data=result['extraction_result'],
                        source_image_path=image_path
                    )
                    result['database_result'] = {
                        'document_id': document_id,
                        'status': 'success'
                    }
                except Exception as e:
                    result['errors'].append(f"Database insertion failed: {str(e)}")
                    logger.error(f"Database insertion failed: {str(e)}")
            else:
                if not self.db:
                    logger.warning("Database not available")
                elif not result['extraction_result']:
                    logger.warning("No extraction result to store")
            
            # Step 5: Accuracy Evaluation
            if self.evaluator and result['ocr_result']:
                logger.info("Step 5: Computing OCR accuracy metrics...")
                
                ocr_text = ' '.join(result['ocr_result']['raw_text'])
                
                eval_result = self.evaluator.evaluate_single_document(
                    Path(image_path).name,
                    ocr_text
                )
                result['evaluation_result'] = eval_result
            else:
                if not self.evaluator:
                    logger.warning("Evaluator not available")
                else:
                    logger.warning("No OCR result to evaluate")
            
            # Print final summary
            self._print_document_summary(result)
            
            self.results['processed_documents'].append(result)
            
        except Exception as e:
            error_msg = f"Error processing document: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            self.results['errors'].append({
                'image_path': image_path,
                'error': error_msg
            })
        
        return result
    
    def process_batch(
        self,
        image_paths: List[str],
        source_language: str = 'hin',
        target_language: str = 'eng'
    ) -> List[Dict[str, Any]]:
        """
        Process multiple documents.
        
        Args:
            image_paths: List of paths to input images
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            List of processing results
        """
        logger.info(f"\n\nProcessing batch of {len(image_paths)} documents\n")
        
        batch_results = []
        
        for image_path in image_paths:
            try:
                result = self.process_document(
                    image_path,
                    source_language=source_language,
                    target_language=target_language
                )
                batch_results.append(result)
            except Exception as e:
                logger.error(f"Critical error processing {image_path}: {str(e)}")
                continue
        
        return batch_results
    
    def process_dataset(
        self,
        dataset_images_path: Optional[str] = None,
        source_language: str = 'hin',
        target_language: str = 'eng'
    ) -> Dict[str, Any]:
        """
        Process all images from the dataset directory.
        
        Args:
            dataset_images_path: Path to images directory
            source_language: Source language code
            target_language: Target language code
            
        Returns:
            Dictionary with batch processing results
        """
        if dataset_images_path is None:
            backend_dir = Path(__file__).parent
            # Use existing Dataset directory with language subdirectories
            dataset_images_path = str(backend_dir / 'Dataset' / 'verified_twice')
        
        images_dir = Path(dataset_images_path)
        
        if not images_dir.exists():
            logger.error(f"Images directory not found: {images_dir}")
            return {
                'error': f'Images directory not found: {images_dir}',
                'documents_processed': 0
            }
        
        # Find all image files
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(images_dir.glob(f'*{ext}'))
            image_files.extend(images_dir.glob(f'*{ext.upper()}'))
        
        image_files = sorted(list(set(image_files)))  # Remove duplicates and sort
        
        logger.info(f"Found {len(image_files)} images in dataset")
        
        if not image_files:
            logger.warning("No images found in dataset directory")
            return {
                'documents_processed': 0,
                'warning': 'No images found in dataset directory'
            }
        
        # Process batch
        batch_results = self.process_batch(
            [str(f) for f in image_files[:5]],  # Process first 5 for demo
            source_language=source_language,
            target_language=target_language
        )
        
        return {
            'total_images_found': len(image_files),
            'documents_processed': len(batch_results),
            'results': batch_results
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline processing statistics"""
        stats = {
            'total_documents_processed': len(self.results['processed_documents']),
            'total_errors': len(self.results['errors']),
            'processing_timestamp': datetime.now().isoformat(),
        }
        
        # Add database statistics if available
        if self.db:
            db_stats = self.db.get_statistics()
            stats['database_stats'] = db_stats
        
        # Calculate OCR metrics
        if self.results['processed_documents']:
            eval_results = [
                r.get('evaluation_result')
                for r in self.results['processed_documents']
                if r.get('evaluation_result') and r['evaluation_result'].get('cer') is not None
            ]
            
            if eval_results:
                avg_cer = sum(r['cer'] for r in eval_results) / len(eval_results)
                avg_wer = sum(r['wer'] for r in eval_results) / len(eval_results)
                
                stats['ocr_metrics'] = {
                    'average_cer': avg_cer,
                    'average_wer': avg_wer,
                    'evaluated_documents': len(eval_results)
                }
        
        return stats
    
    def save_results(self, output_path: str = 'pipeline_results.json'):
        """Save pipeline results to JSON file"""
        try:
            stats = self.get_statistics()
            
            output = {
                'pipeline_statistics': stats,
                'documents': self.results['processed_documents'],
                'errors': self.results['errors']
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Results saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.db:
            self.db.close()
        logger.info("Pipeline cleanup completed")
    
    def _print_document_summary(self, result: Dict[str, Any]):
        """Print final document processing summary"""
        print("\n" + "="*70)
        print("DOCUMENT PROCESSING COMPLETE")
        print("="*70)
        
        print("\nProcessing Steps Status:")
        print("-"*70)
        print(f"✓ OCR: {'SUCCESS' if result['ocr_result'] else 'FAILED'}")
        print(f"✓ Translation: {'SUCCESS' if result['translation_result'] else 'FAILED'}")
        print(f"✓ Extraction: {'SUCCESS' if result['extraction_result'] else 'FAILED'}")
        print(f"✓ Database: {'SUCCESS' if result['database_result'] else 'SKIPPED'}")
        print(f"✓ Evaluation: {'SUCCESS' if result['evaluation_result'] else 'SKIPPED'}")
        
        if result['errors']:
            print("\nErrors:")
            for error in result['errors']:
                print(f"  ⚠ {error}")
        
        print("\n" + "="*70 + "\n")


def main():
    """Main entry point for pipeline execution"""
    logger.info("Starting Multilingual Document Processing Pipeline")
    
    # Initialize pipeline
    pipeline = DocumentProcessingPipeline(device='cpu')  # Use CPU for compatibility
    
    # Example: Process from existing Dataset directory
    sample_image = None
    
    # Try to find images from the Dataset directory structure
    backend_dir = Path(__file__).parent
    dataset_root = backend_dir / 'Dataset' / 'verified_twice'
    
    if dataset_root.exists():
        # Look for images in language subdirectories
        for lang_dir in dataset_root.iterdir():
            if lang_dir.is_dir():
                images = list(lang_dir.glob('*.png')) + list(lang_dir.glob('*.jpg'))
                if images:
                    sample_image = str(images[0])
                    break
    
    if sample_image and Path(sample_image).exists():
        logger.info(f"Processing sample image: {sample_image}")
        result = pipeline.process_document(sample_image)
        
        # Get statistics
        stats = pipeline.get_statistics()
        logger.info(f"\nPipeline Statistics:\n{json.dumps(stats, indent=2)}")
        
        # Save results
        pipeline.save_results('pipeline_results.json')
    else:
        logger.info("\nNo sample images found.")
        logger.info("Dataset directory found at: backend/Dataset/verified_twice/")
        logger.info("  Available language directories: assamese, gujarati, hindi, kannada,")
        logger.info("                                 malayalam, marathi, odia, punjabi,")
        logger.info("                                 tamil, telugu, urdu")
        logger.info("\nTo process documents:")
        logger.info("  1. Images are in: backend/Dataset/verified_twice/{language}/")
        logger.info("  2. Run: python pipeline.py")
        logger.info("\nExample usage:")
        logger.info("  pipeline = DocumentProcessingPipeline()")
        logger.info("  result = pipeline.process_document('path/to/image.png')")
        logger.info("  dataset_results = pipeline.process_dataset()")  # Will process entire Dataset directory
        logger.info("  \n  # Process specific language:")
        logger.info("  batch_results = pipeline.process_batch([")
        logger.info("    'backend/Dataset/verified_twice/hindi/img.png',")
        logger.info("    'backend/Dataset/verified_twice/tamil/img.png'")
        logger.info("  ])")
    
    # Cleanup
    pipeline.cleanup()
    logger.info("Pipeline execution completed")


if __name__ == '__main__':
    main()
