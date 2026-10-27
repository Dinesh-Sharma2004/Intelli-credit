"""
IndicTrOCR Integration Service
Performs OCR on Indian language documents using IndicTrOCR model
"""

import logging
import numpy as np
import cv2
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image
from datetime import datetime
import sys

logger = logging.getLogger(__name__)

# Lazy import to avoid circular dependency issues
TRANSFORMERS_AVAILABLE = True
try:
    import torch
except:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("PyTorch not available")


class IndicOCRService:
    """
    OCR Service using IndicTrOCR for Indian languages
    Supports: Assamese, Bengali, Gujarati, Hindi, Kannada, Malayalam, 
              Marathi, Odia, Punjabi, Tamil, Telugu, Urdu
    """
    
    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or Path(__file__).parent.parent / "models" / "indic_trocr"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.models = {}  # Cache for loaded models
        self.processors = {}
        self.tokenizers = {}
        
        # Map language codes to IndicTrOCR model IDs
        self.language_models = {
            'assamese': 'ai4bharat/IndicTrOCR-Assamese_v0',
            'bengali': 'ai4bharat/IndicTrOCR-Bengali_v0',
            'gujarati': 'ai4bharat/IndicTrOCR-Gujarati_v0',
            'hindi': 'ai4bharat/IndicTrOCR-Hindi_v0',
            'kannada': 'ai4bharat/IndicTrOCR-Kannada_v0',
            'malayalam': 'ai4bharat/IndicTrOCR-Malayalam_v0',
            'marathi': 'ai4bharat/IndicTrOCR-Marathi_v0',
            'odia': 'ai4bharat/IndicTrOCR-Odia_v0',
            'punjabi': 'ai4bharat/IndicTrOCR-Punjabi_v0',
            'tamil': 'ai4bharat/IndicTrOCR-Tamil_v0',
            'telugu': 'ai4bharat/IndicTrOCR-Telugu_v0',
            'urdu': 'ai4bharat/IndicTrOCR-Urdu_v0',
            'english': 'ai4bharat/IndicTrOCR-English_v0'
        }
        
        logger.info(f"IndicOCR Service initialized. Device: {self.device}")
    
    def load_model(self, language: str) -> Tuple:
        """Load model for specific language"""
        try:
            from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
        except ImportError as e:
            logger.error(f"Transformers import failed: {e}")
            return None, None, None
        
        lang_lower = language.lower()
        
        if lang_lower in self.models:
            return self.models[lang_lower], self.processors[lang_lower], self.tokenizers[lang_lower]
        
        if lang_lower not in self.language_models:
            logger.warning(f"Language {language} not supported. Using Hindi model.")
            lang_lower = 'hindi'
        
        model_id = self.language_models[lang_lower]
        
        try:
            logger.info(f"Loading model for {language}: {model_id}")
            
            # Load model
            model = VisionEncoderDecoderModel.from_pretrained(model_id, trust_remote_code=True)
            model = model.to(self.device)
            model.eval()
            
            # Load processor
            processor = ViTImageProcessor.from_pretrained(model_id, trust_remote_code=True)
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            
            # Cache the models
            self.models[lang_lower] = model
            self.processors[lang_lower] = processor
            self.tokenizers[lang_lower] = tokenizer
            
            logger.info(f"Model loaded successfully for {language}")
            return model, processor, tokenizer
            
        except Exception as e:
            logger.error(f"Error loading model for {language}: {e}")
            raise
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Load and preprocess image for OCR"""
        try:
            image = Image.open(image_path).convert('RGB')
            image_array = np.array(image)
            
            # Apply preprocessing
            # 1. Denoise
            image_array = cv2.fastNlMeansDenoisingColored(image_array, h=10)
            
            # 2. Edge enhancement
            kernel = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
            image_array = cv2.filter2D(image_array, -1, kernel)
            
            # 3. Normalize
            image_array = image_array.astype(np.float32) / 255.0
            
            return image_array
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {e}")
            raise
    
    def extract_text_from_image(self, image_path: str, language: str = 'hindi') -> Dict:
        """
        Extract text from single image using IndicTrOCR
        
        Returns:
            Dict with keys: text, confidence, language, processing_time
        """
        try:
            start_time = datetime.utcnow()
            
            # Load model if not already loaded
            model, processor, tokenizer = self.load_model(language)
            
            # Preprocess image
            image_array = self.preprocess_image(image_path)
            image = Image.fromarray((image_array * 255).astype(np.uint8))
            
            # Process image
            pixel_values = processor(image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            
            # Generate text
            with torch.no_grad():
                generated_ids = model.generate(pixel_values, max_length=100)
            
            # Decode
            generated_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # Calculate confidence based on character-level certainty
            # This is a simplified metric - actual confidence comes from model's attention weights
            confidence = self.calculate_confidence(generated_text, image_array)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                'text': generated_text,
                'confidence': min(0.99, max(0.45, confidence)),  # Clamp between 0.45 and 0.99
                'language': language,
                'processing_time': processing_time,
                'character_count': len(generated_text),
                'word_count': len(generated_text.split()),
            }
            
            logger.info(f"OCR completed for {language}: {len(generated_text)} characters, confidence: {confidence:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise
    
    def calculate_confidence(self, text: str, image_array: np.ndarray) -> float:
        """
        Calculate confidence score for OCR result
        Based on text clarity, image quality, and character count
        """
        if not text:
            return 0.3
        
        # Image quality metrics
        image_uint8 = (image_array * 255).astype(np.uint8)
        
        # Calculate Laplacian variance (sharpness)
        gray = cv2.cvtColor(image_uint8, cv2.COLOR_RGB2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(1.0, laplacian_var / 500)
        
        # Calculate brightness
        brightness = gray.mean() / 255.0
        brightness_score = 1.0 - abs(brightness - 0.5) * 2  # Optimal around 0.5
        
        # Text quality (length and diversity)
        text_score = min(1.0, len(text) / 100)
        
        # Combine metrics
        confidence = (
            sharpness_score * 0.4 +
            brightness_score * 0.3 +
            text_score * 0.3
        )
        
        return min(0.99, max(0.45, confidence))
    
    def extract_text_from_pdf(self, pdf_path: str, language: str = 'hindi') -> Dict:
        """
        Extract text from PDF by converting to images
        
        Returns:
            Dict with keys: pages, total_text, average_confidence, languages
        """
        try:
            import pdf2image
            
            # Convert PDF to images
            images = pdf2image.convert_from_path(pdf_path)
            
            results = []
            total_confidence = 0
            
            for page_num, image in enumerate(images, 1):
                # Save image temporarily
                temp_image_path = f"/tmp/page_{page_num}.png"
                image.save(temp_image_path)
                
                # Extract text
                page_result = self.extract_text_from_image(temp_image_path, language)
                page_result['page_number'] = page_num
                results.append(page_result)
                total_confidence += page_result['confidence']
            
            average_confidence = total_confidence / len(results) if results else 0.5
            all_text = ' '.join([r['text'] for r in results])
            
            return {
                'pages': results,
                'total_text': all_text,
                'average_confidence': average_confidence,
                'page_count': len(results),
                'total_characters': len(all_text),
                'total_words': len(all_text.split()),
                'language': language,
                'processing_time': sum(r['processing_time'] for r in results)
            }
            
        except ImportError:
            logger.warning("pdf2image not installed. Install with: pip install pdf2image")
            raise
        except Exception as e:
            logger.error(f"Error extracting from PDF {pdf_path}: {e}")
            raise
    
    def detect_language(self, image_path: str) -> str:
        """
        Detect language in image
        Uses image analysis and character recognition patterns
        """
        try:
            # Try all supported languages and pick the one with highest confidence
            best_language = 'hindi'
            best_confidence = 0
            
            for language in ['hindi', 'tamil', 'telugu', 'kannada', 'malayalam', 'bengali']:
                try:
                    result = self.extract_text_from_image(image_path, language)
                    if result['confidence'] > best_confidence:
                        best_confidence = result['confidence']
                        best_language = language
                except:
                    continue
            
            logger.info(f"Detected language: {best_language} (confidence: {best_confidence:.3f})")
            return best_language
            
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return 'hindi'  # Default fallback


# Singleton instance
_ocr_service = None

def get_ocr_service() -> IndicOCRService:
    """Get or create OCR service singleton"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = IndicOCRService()
    return _ocr_service
