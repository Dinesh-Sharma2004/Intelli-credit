"""
OCR Module using IndicTrOCR for multilingual text extraction

This module handles:
- Loading IndicTrOCR model from local backend/models directory
- Extracting multilingual text from document images
- Processing Indian languages: Hindi, Telugu, Tamil, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Urdu, English
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import logging

import cv2
import numpy as np
import torch
from PIL import Image

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class IndicTrOCR:
    """
    Load and use IndicTrOCR model for multilingual text extraction.
    
    Supported languages:
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
    """
    
    # Supported language codes
    SUPPORTED_LANGUAGES = {
        'hin': 'Hindi',
        'tel': 'Telugu',
        'tam': 'Tamil',
        'ben': 'Bengali',
        'mar': 'Marathi',
        'guj': 'Gujarati',
        'kan': 'Kannada',
        'mal': 'Malayalam',
        'pan': 'Punjabi',
        'urd': 'Urdu',
        'eng': 'English'
    }
    
    def __init__(self, model_path: Optional[str] = None, device: str = 'cuda'):
        """
        Initialize IndicTrOCR model.
        
        Args:
            model_path: Path to local IndicTrOCR model. Defaults to backend/models/indic_trocr
            device: Device to run model on ('cuda' or 'cpu')
        """
        self.device = device if torch.cuda.is_available() else 'cpu'
        if device == 'cuda' and not torch.cuda.is_available():
            logger.warning("CUDA not available. Falling back to CPU.")
        
        if model_path is None:
            model_path = self._get_default_model_path()
        
        self.model_path = Path(model_path)
        self.model = None
        self.processor = None
        
        self._load_model()
    
    def _get_default_model_path(self) -> str:
        """Get default model path from backend/models/indic_trocr"""
        backend_dir = Path(__file__).parent.parent  # backend directory
        model_dir = backend_dir / 'models' / 'indic_trocr'
        return str(model_dir)
    
    def _load_model(self):
        """Load IndicTrOCR model from local directory."""
        logger.info(f"Loading IndicTrOCR model from: {self.model_path}")
        
        if not self.model_path.exists():
            logger.error(f"Model path does not exist: {self.model_path}")
            logger.info(f"Clone the model using:")
            logger.info(f"git clone https://github.com/AI4Bharat/IndicTrOCR {self.model_path}")
            raise FileNotFoundError(f"Model path does not exist: {self.model_path}")
        
        try:
            # Import from transformers for TrOCR
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            
            # Load processor and model from local directory
            self.processor = TrOCRProcessor.from_pretrained(str(self.model_path))
            self.model = VisionEncoderDecoderModel.from_pretrained(str(self.model_path))
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("IndicTrOCR model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            logger.info("Make sure to clone the IndicTrOCR repository:")
            logger.info(f"git clone https://github.com/AI4Bharat/IndicTrOCR {self.model_path}")
            raise
    
    def preprocess_image(self, image_path: str) -> Image.Image:
        """
        Preprocess image for OCR.
        
        Args:
            image_path: Path to input image
            
        Returns:
            PIL Image object
        """
        try:
            image = Image.open(image_path).convert('RGB')
            logger.debug(f"Loaded image: {image_path}, size: {image.size}")
            return image
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {str(e)}")
            raise
    
    def extract_text(self, image_path: str) -> Dict[str, List[str]]:
        """
        Extract multilingual text from document image using IndicTrOCR.
        
        Args:
            image_path: Path to input image
            
        Returns:
            Dictionary with extracted text lines and metadata
        """
        logger.info(f"Processing image: {Path(image_path).name}")
        
        try:
            # Preprocess image
            image = self.preprocess_image(image_path)
            
            # Prepare pixel values for model
            pixel_values = self.processor(images=image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            
            # Run inference
            with torch.no_grad():
                outputs = self.model.generate(pixel_values, max_length=300)
            
            # Decode predictions
            predicted_texts = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            # Split into lines (simple approach - split by newline or use line detection)
            text_lines = self._segment_text_into_lines(predicted_texts)
            
            result = {
                "image_path": image_path,
                "raw_text": text_lines,
                "full_text": predicted_texts,
                "language_detected": self._detect_language(predicted_texts),
                "num_lines": len(text_lines)
            }
            
            # Print console output
            self._print_console_output(image_path, text_lines)
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {str(e)}")
            raise
    
    def extract_text_batch(self, image_paths: List[str]) -> List[Dict]:
        """
        Extract text from multiple images.
        
        Args:
            image_paths: List of paths to input images
            
        Returns:
            List of result dictionaries
        """
        results = []
        for image_path in image_paths:
            try:
                result = self.extract_text(image_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {str(e)}")
                continue
        
        return results
    
    def _segment_text_into_lines(self, text: str, max_words_per_line: int = 10) -> List[str]:
        """
        Segment extracted text into lines for better readability.
        
        Args:
            text: Full extracted text
            max_words_per_line: Maximum words per line
            
        Returns:
            List of text lines
        """
        if not text:
            return []
        
        # Simple line splitting by common delimiters
        lines = text.split('\n')
        result_lines = []
        
        for line in lines:
            if line.strip():
                # Split long lines into manageable chunks
                words = line.split()
                current_line = []
                
                for word in words:
                    current_line.append(word)
                    if len(current_line) >= max_words_per_line:
                        result_lines.append(' '.join(current_line))
                        current_line = []
                
                if current_line:
                    result_lines.append(' '.join(current_line))
        
        return result_lines if result_lines else [text]
    
    def _detect_language(self, text: str) -> List[str]:
        """
        Detect languages in extracted text based on script characteristics.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected language codes
        """
        # Script ranges for Indian languages
        script_ranges = {
            'hin': (0x0900, 0x097F),  # Devanagari
            'ben': (0x0980, 0x09FF),  # Bengali
            'guj': (0x0A80, 0x0AFF),  # Gujarati
            'pan': (0x0A00, 0x0A7F),  # Gurmukhi
            'tel': (0x0C60, 0x0C7F),  # Telugu
            'tam': (0x0B80, 0x0BFF),  # Tamil
            'kan': (0x0C80, 0x0CFF),  # Kannada
            'mal': (0x0D00, 0x0D7F),  # Malayalam
            'mar': (0x0900, 0x097F),  # Marathi (Devanagari)
            'urd': (0x0600, 0x06FF),  # Arabic/Urdu
        }
        
        detected = []
        for lang_code, (start, end) in script_ranges.items():
            if any(start <= ord(char) <= end for char in text):
                detected.append(lang_code)
        
        # Default to English if no specific script detected
        if not detected:
            detected.append('eng')
        
        return detected
    
    def _print_console_output(self, image_path: str, text_lines: List[str]):
        """Print formatted console output for detected text."""
        print("\n" + "="*60)
        print(f"Processing image: {Path(image_path).name}")
        print("="*60)
        print("Detected OCR text:")
        print("-"*60)
        for line in text_lines:
            print(line)
        print("-"*60 + "\n")
