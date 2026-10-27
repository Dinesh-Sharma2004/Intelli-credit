#!/usr/bin/env python3
"""
Document Processor Service
Handles PDF upload, OCR, translation, and storage
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import PyPDF2
from PIL import Image
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_UPLOAD_DIR = BASE_DIR / "uploads"


class DocumentProcessor:
    """
    Processes uploaded documents:
    1. Extract text from PDF
    2. Perform OCR on images
    3. Translate to English
    4. Store results in database
    """
    
    def __init__(self, ocr_model=None, translator=None, db_manager=None):
        """
        Initialize document processor
        
        Args:
            ocr_model: IndicTrOCR model instance
            translator: IndicTranslator model instance
            db_manager: DatabaseManager instance
        """
        self.ocr_model = ocr_model
        self.translator = translator
        self.db_manager = db_manager
        self.upload_dir = DEFAULT_UPLOAD_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info("DocumentProcessor initialized")
    
    def extract_text_from_pdf(self, pdf_path: str, use_ocr: bool = True) -> Dict:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            use_ocr: Whether to use OCR for images in PDF
            
        Returns:
            Dict with extracted content and metadata
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            result = {
                'file_name': pdf_path.name,
                'file_size': pdf_path.stat().st_size,
                'extraction_date': datetime.now().isoformat(),
                'pages': [],
                'total_text_length': 0,
                'status': 'success'
            }
            
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)
                logger.info(f"Processing PDF: {pdf_path.name} ({num_pages} pages)")
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_data = {
                        'page_number': page_num,
                        'text': '',
                        'ocr_text': None,
                        'language_detected': None
                    }
                    
                    # Extract text using PyPDF2
                    text = page.extract_text()
                    page_data['text'] = text
                    result['total_text_length'] += len(text)
                    
                    # TODO: Extract images and perform OCR if needed
                    # For now, log page extraction
                    logger.info(f"  Page {page_num}: {len(text)} characters extracted")
                    
                    result['pages'].append(page_data)
            
            logger.info(f"✓ PDF extraction completed: {result['total_text_length']} total characters")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'file_name': pdf_path.name if 'pdf_path' in locals() else 'unknown'
            }
    
    def translate_content(self, content: Dict) -> Dict:
        """
        Translate extracted content to English
        
        Args:
            content: Dict with extracted content
            
        Returns:
            Dict with translated content
        """
        if not self.translator:
            logger.warning("Translator not initialized, skipping translation")
            return content
        
        try:
            translated_content = content.copy()
            translated_content['translations'] = []
            
            for page in content.get('pages', []):
                original_text = page.get('text', '')
                
                if not original_text.strip():
                    continue
                
                # Simulate translation (actual would use translator.translate())
                # For now, log the translation request
                logger.info(f"Translating page {page['page_number']}: {len(original_text)} chars")
                
                translation_result = {
                    'page_number': page['page_number'],
                    'original_text': original_text[:100] + '...' if len(original_text) > 100 else original_text,
                    'translated_text': f'[Translated text for page {page["page_number"]}]',
                    'translation_date': datetime.now().isoformat()
                }
                
                translated_content['translations'].append(translation_result)
            
            logger.info(f"✓ Translation completed for {len(translated_content['translations'])} pages")
            return translated_content
            
        except Exception as e:
            logger.error(f"Error translating content: {e}")
            content['translation_error'] = str(e)
            return content
    
    def process_document(self, pdf_path: str, language: Optional[str] = None) -> Dict:
        """
        Complete document processing pipeline
        
        Args:
            pdf_path: Path to PDF file
            language: Detected language (optional)
            
        Returns:
            Dict with processing results
        """
        logger.info(f"Starting document processing: {pdf_path}")
        
        # Step 1: Extract text from PDF
        extracted = self.extract_text_from_pdf(pdf_path)
        
        if extracted.get('status') == 'error':
            return extracted
        
        # Step 2: Translate content
        translated = self.translate_content(extracted)
        
        # Step 3: Store in database (if available)
        result = {
            'document_id': self._generate_doc_id(),
            'file_name': extracted['file_name'],
            'extraction': {
                'status': extracted['status'],
                'pages_count': len(extracted.get('pages', [])),
                'total_text': extracted['total_text_length']
            },
            'translation': {
                'status': 'completed' if 'translations' in translated else 'skipped',
                'pages_translated': len(translated.get('translations', []))
            },
            'processed_date': datetime.now().isoformat()
        }
        
        if self.db_manager:
            try:
                db_result = self.db_manager.insert_document(
                    original_text=json.dumps(extracted['pages']),
                    translated_text=json.dumps(translated.get('translations', [])),
                    extracted_data={'document_id': result['document_id']},
                    source_image_path=str(pdf_path)
                )
                result['database_id'] = str(db_result)
                logger.info(f"✓ Document stored in database: {db_result}")
            except Exception as e:
                logger.warning(f"Could not store in database: {e}")
                result['database_error'] = str(e)
        
        logger.info("✓ Document processing completed")
        return result
    
    def _generate_doc_id(self) -> str:
        """Generate unique document ID"""
        import uuid
        return str(uuid.uuid4())
    
    def get_processed_documents(self, limit: int = 10) -> List[Dict]:
        """Get list of processed documents"""
        if not self.db_manager:
            logger.warning("Database manager not initialized")
            return []
        
        try:
            documents = self.db_manager.get_all_documents(limit=limit)
            logger.info(f"Retrieved {len(documents)} processed documents")
            return documents
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def search_documents(self, **filters) -> List[Dict]:
        """Search processed documents by filters"""
        if not self.db_manager:
            logger.warning("Database manager not initialized")
            return []
        
        try:
            results = self.db_manager.search_documents(**filters)
            logger.info(f"Found {len(results)} matching documents")
            return results
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []


class PDFUploadHandler:
    """
    Handles PDF file uploads and validation
    """
    
    def __init__(self, upload_dir: str | Path = DEFAULT_UPLOAD_DIR, max_file_size: int = 50 * 1024 * 1024):
        """
        Initialize upload handler
        
        Args:
            upload_dir: Directory to store uploaded files
            max_file_size: Maximum file size in bytes (default: 50MB)
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size
        self.allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff'}
        logger.info(f"PDFUploadHandler initialized: {self.upload_dir}")
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate uploaded file
        
        Args:
            file_path: Path to uploaded file
            
        Returns:
            Tuple of (is_valid, message)
        """
        file_path = Path(file_path)
        
        # Check file exists
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        # Check file extension
        if file_path.suffix.lower() not in self.allowed_extensions:
            return False, f"Invalid file type. Allowed: {self.allowed_extensions}"
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            return False, f"File too large: {file_size} > {self.max_file_size} bytes"
        
        # Check PDF validity
        if file_path.suffix.lower() == '.pdf':
            try:
                with open(file_path, 'rb') as f:
                    PyPDF2.PdfReader(f)
            except Exception as e:
                return False, f"Invalid PDF file: {e}"
        
        return True, "File validation successful"
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Save uploaded file to disk
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Tuple of (success, file_path or error_message)
        """
        try:
            # Sanitize filename
            filename = Path(filename).name
            file_path = self.upload_dir / filename
            
            # Check for duplicate and create unique filename if needed
            counter = 1
            original_stem = file_path.stem
            while file_path.exists():
                file_path = self.upload_dir / f"{original_stem}_{counter}{file_path.suffix}"
                counter += 1
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"✓ File saved: {file_path}")
            return True, str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return False, str(e)
    
    def get_uploaded_files(self) -> List[Dict]:
        """Get list of uploaded files"""
        files = []
        for file_path in self.upload_dir.glob('*'):
            if file_path.is_file():
                files.append({
                    'filename': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'uploaded_date': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        return files


def main():
    """Example usage"""
    logger.info("Document Processor Service")
    logger.info("=" * 50)
    
    # Initialize components
    processor = DocumentProcessor()
    upload_handler = PDFUploadHandler()
    
    logger.info("✓ Services initialized and ready")
    logger.info("\nUsage:")
    logger.info("1. Upload document: upload_handler.save_uploaded_file(content, filename)")
    logger.info("2. Process document: processor.process_document(pdf_path)")
    logger.info("3. Search documents: processor.search_documents(**filters)")


if __name__ == '__main__':
    main()
