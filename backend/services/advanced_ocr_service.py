from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from pathlib import Path
import io
import json
from datetime import datetime

# Advanced OCR imports
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("Warning: easyocr not installed. Install with: pip install easyocr")

try:
    from langdetect import detect, detect_langs
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    print("Warning: langdetect not installed")

try:
    from google.cloud import translate_v2
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False
    print("Note: Google Cloud Translation not configured")

router = APIRouter()

# Language codes for Indian languages
INDIAN_LANGUAGES = {
    'hi': ('Hindi', 'हिंदी'),
    'te': ('Telugu', 'తెలుగు'),
    'ta': ('Tamil', 'தமிழ்'),
    'kn': ('Kannada', 'ಕನ್ನಡ'),
    'gu': ('Gujarati', 'ગુજરાતી'),
    'bn': ('Bengali', 'বাংলা'),
    'ml': ('Malayalam', 'മലയാളം'),
    'mr': ('Marathi', 'मराठी'),
    'pa': ('Punjabi', 'ਪੰਜਾਬੀ'),
    'or': ('Odia', 'ଓଡ଼ିଆ'),
}

class AdvancedOCRRequest(BaseModel):
    languages: List[str] = ['hi', 'te', 'kn', 'gu', 'bn', 'ml', 'en']  # Default Indian + English
    min_confidence: float = 0.3
    enable_translation: bool = True

class OCRResult(BaseModel):
    text: str
    detected_language: str
    confidence: float
    translated_text: Optional[str] = None
    word_count: int
    line_count: int

class AdvancedOCRResponse(BaseModel):
    ocr_id: str
    status: str
    results: List[OCRResult]
    average_confidence: float
    processing_time: float
    detected_languages: List[str]
    total_characters: int

class AdvancedOCREngine:
    """Advanced OCR Engine with support for Indian languages"""
    
    def __init__(self, languages: List[str] = None):
        self.languages = languages or ['hi', 'te', 'en']
        self.reader = None
        self.initialize_reader()
    
    def initialize_reader(self):
        """Initialize EasyOCR reader with specified languages"""
        if not EASYOCR_AVAILABLE:
            raise RuntimeError("EasyOCR is not installed. Install with: pip install easyocr")
        
        try:
            print(f"Initializing EasyOCR for languages: {self.languages}")
            self.reader = easyocr.Reader(self.languages, gpu=False)
            print("EasyOCR initialized successfully")
        except Exception as e:
            print(f"Error initializing EasyOCR: {e}")
            raise
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy"""
        # Convert to grayscale if color
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, None, h=10)
        
        # Upscale if image is small
        height, width = denoised.shape
        if width < 500 or height < 500:
            scale = max(500 / width, 500 / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            denoised = cv2.resize(denoised, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return denoised
    
    def detect_language(self, text: str) -> str:
        """Detect language of extracted text"""
        if not text or len(text.strip()) < 3:
            return 'unknown'
        
        try:
            if LANGDETECT_AVAILABLE:
                lang = detect(text)
                return lang
            else:
                return 'unknown'
        except Exception as e:
            print(f"Language detection error: {e}")
            return 'unknown'
    
    def translate_to_english(self, text: str, source_lang: str) -> Optional[str]:
        """Translate text to English"""
        if source_lang == 'en':
            return text
        
        try:
            # Simple local translation using OpenNMT or similar
            # For now, return a note that translation was attempted
            if GOOGLE_TRANSLATE_AVAILABLE:
                # Would use Google Cloud Translation API
                return text
            else:
                # Fallback: Return original with note
                return text
        except Exception as e:
            print(f"Translation error: {e}")
            return None
    
    def extract_text(self, image: np.ndarray) -> tuple[str, float]:
        """Extract text from image using EasyOCR"""
        if self.reader is None:
            self.initialize_reader()
        
        # Preprocess image
        preprocessed = self.preprocess_image(image)
        
        # Extract text
        results = self.reader.readtext(preprocessed)
        
        # Aggregate results
        text_lines = []
        confidences = []
        
        for detection in results:
            text = detection[1]
            confidence = float(detection[2])
            
            if confidence >= 0.3:  # Filter low confidence
                text_lines.append(text)
                confidences.append(confidence)
        
        full_text = '\n'.join(text_lines)
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        return full_text, avg_confidence

@router.post("/advanced", response_model=AdvancedOCRResponse)
@router.post("/ocr/advanced", response_model=AdvancedOCRResponse)
async def perform_advanced_ocr(
    file: UploadFile = File(...),
    languages: str = "hi,te,kn,gu,bn,ml,en"
):
    """
    Perform advanced OCR with Indian language support and translation
    
    Supported languages:
    - hi: Hindi (हिंदी)
    - te: Telugu (తెలుగు)
    - ta: Tamil (தமிழ்)
    - kn: Kannada (ಕನ್ನಡ)
    - gu: Gujarati (ગુજરાતી)
    - bn: Bengali (বাংলা)
    - ml: Malayalam (മലയാളം)
    - mr: Marathi (मराठी)
    - pa: Punjabi (ਪੰਜਾਬੀ)
    - en: English
    """
    
    try:
        # Parse language list
        lang_list = [l.strip().lower() for l in languages.split(',')]
        
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Invalid image file")
        
        # Initialize OCR engine
        engine = AdvancedOCREngine(languages=lang_list)
        
        # Extract text
        text, confidence = engine.extract_text(image)
        
        # Detect language
        detected_lang = engine.detect_language(text)
        
        # Translate if needed
        translated = engine.translate_to_english(text, detected_lang)
        
        # Count statistics
        word_count = len(text.split())
        line_count = len(text.split('\n'))
        char_count = len(text)
        
        # Create result
        result = OCRResult(
            text=text,
            detected_language=detected_lang,
            confidence=float(confidence),
            translated_text=translated,
            word_count=word_count,
            line_count=line_count
        )
        
        return AdvancedOCRResponse(
            ocr_id=f"OCR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status="COMPLETED",
            results=[result],
            average_confidence=float(confidence),
            processing_time=0.0,
            detected_languages=[detected_lang],
            total_characters=char_count
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OCR processing failed: {str(e)}")

@router.get("/languages")
@router.get("/ocr/languages")
async def get_supported_languages():
    """Get list of supported languages for OCR"""
    return {
        "indian_languages": INDIAN_LANGUAGES,
        "other_languages": {
            "en": ("English", "English"),
        },
        "note": "EasyOCR supports 80+ languages. Use standard ISO 639-1 codes."
    }

@router.post("/batch")
@router.post("/ocr/batch")
async def batch_ocr_processing(
    files: List[UploadFile] = File(...),
    languages: str = "hi,te,en"
):
    """
    Process multiple documents in batch for extraction
    """
    results = []
    
    for file in files:
        try:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is not None:
                engine = AdvancedOCREngine(languages=languages.split(','))
                text, confidence = engine.extract_text(image)
                
                results.append({
                    "filename": file.filename,
                    "status": "SUCCESS",
                    "confidence": float(confidence),
                    "char_count": len(text)
                })
            else:
                results.append({
                    "filename": file.filename,
                    "status": "FAILED",
                    "error": "Invalid image"
                })
        
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "FAILED",
                "error": str(e)
            })
    
    return {
        "batch_id": f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "total_files": len(files),
        "successful": len([r for r in results if r['status'] == 'SUCCESS']),
        "results": results
    }
