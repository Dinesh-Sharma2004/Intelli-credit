"""
Translation Module using IndicTrans2 for multilingual text translation

This module handles:
- Loading IndicTrans2 model from local backend/models directory
- Translating Indian language text to English
- Supporting bidirectional translation between Indian languages
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class IndicTranslator:
    """
    Load and use IndicTrans2 model for multilingual translation.
    
    Supports translation from Indian languages to English and vice versa:
    - Hindi, Telugu, Tamil, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Urdu
    """
    
    # Language codes for IndicTrans2
    LANGUAGE_CODES = {
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
        Initialize IndicTrans2 model.
        
        Args:
            model_path: Path to local IndicTrans2 model. Defaults to backend/models/indictrans2
            device: Device to run model on ('cuda' or 'cpu')
        """
        self.device = device if torch.cuda.is_available() else 'cpu'
        if device == 'cuda' and not torch.cuda.is_available():
            logger.warning("CUDA not available. Falling back to CPU.")
        
        if model_path is None:
            model_path = self._get_default_model_path()
        
        self.model_path = Path(model_path)
        self.tokenizer = None
        self.model = None
        
        self._load_model()
    
    def _get_default_model_path(self) -> str:
        """Get default model path from backend/models/indictrans2"""
        backend_dir = Path(__file__).parent.parent  # backend directory
        model_dir = backend_dir / 'models' / 'indictrans2'
        return str(model_dir)
    
    def _load_model(self):
        """Load IndicTrans2 model from local directory."""
        logger.info(f"Loading IndicTrans2 model from: {self.model_path}")
        
        if not self.model_path.exists():
            logger.error(f"Model path does not exist: {self.model_path}")
            logger.info(f"Clone the model using:")
            logger.info(f"git clone https://github.com/AI4Bharat/IndicTrans2 {self.model_path}")
            raise FileNotFoundError(f"Model path does not exist: {self.model_path}")
        
        try:
            # Load tokenizer and model from local directory
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                trust_remote_code=True
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                str(self.model_path),
                trust_remote_code=True
            )
            
            self.model.to(self.device)
            self.model.eval()
            
            logger.info("IndicTrans2 model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            logger.info("Make sure to clone the IndicTrans2 repository:")
            logger.info(f"git clone https://github.com/AI4Bharat/IndicTrans2 {self.model_path}")
            raise
    
    def translate(
        self,
        text: str,
        source_lang: str = 'hin',
        target_lang: str = 'eng',
        batch_size: int = 32,
        num_beams: int = 5
    ) -> Dict[str, str]:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'hin' for Hindi)
            target_lang: Target language code (e.g., 'eng' for English)
            batch_size: Batch size for translation
            num_beams: Number of beams for beam search
            
        Returns:
            Dictionary with translated text and metadata
        """
        if not text.strip():
            logger.warning("Empty text provided for translation")
            return {"translated_text": "", "source_lang": source_lang, "target_lang": target_lang}
        
        try:
            # Format input with language code prefix (IndicTrans2 convention)
            # Example: "<2en>Hello" for English translation
            lang_prefix = f"<2{target_lang}>"
            input_text = f"{lang_prefix} {text}"
            
            # Tokenize input
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            
            inputs = {key: val.to(self.device) for key, val in inputs.items()}
            
            # Generate translation
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    num_beams=num_beams,
                    early_stopping=True,
                    max_length=512,
                    min_length=1
                )
            
            # Decode translation
            translated_text = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            )
            
            result = {
                "original_text": text,
                "translated_text": translated_text,
                "source_language": self.LANGUAGE_CODES.get(source_lang, source_lang),
                "target_language": self.LANGUAGE_CODES.get(target_lang, target_lang),
                "source_lang_code": source_lang,
                "target_lang_code": target_lang
            }
            
            # Print console output
            self._print_translation_output(text, translated_text, source_lang, target_lang)
            
            return result
            
        except Exception as e:
            logger.error(f"Error translating text: {str(e)}")
            raise
    
    def translate_batch(
        self,
        texts: List[str],
        source_lang: str = 'hin',
        target_lang: str = 'eng',
        batch_size: int = 32,
        num_beams: int = 5
    ) -> List[Dict]:
        """
        Translate multiple texts.
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            batch_size: Batch size for translation
            num_beams: Number of beams for beam search
            
        Returns:
            List of translation result dictionaries
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            for text in batch:
                try:
                    result = self.translate(text, source_lang, target_lang, batch_size, num_beams)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to translate text: {str(e)}")
                    results.append({
                        "original_text": text,
                        "translated_text": None,
                        "error": str(e)
                    })
        
        return results
    
    def detect_and_translate(
        self,
        text: str,
        target_lang: str = 'eng',
        num_beams: int = 5
    ) -> Dict[str, str]:
        """
        Auto-detect source language and translate to target language.
        
        Args:
            text: Text to translate
            target_lang: Target language code
            num_beams: Number of beams for beam search
            
        Returns:
            Dictionary with translation result
        """
        # Simple language detection based on script
        source_lang = self._detect_source_language(text)
        
        logger.info(f"Detected source language: {self.LANGUAGE_CODES.get(source_lang, source_lang)}")
        
        return self.translate(text, source_lang, target_lang, num_beams=num_beams)
    
    def _detect_source_language(self, text: str) -> str:
        """
        Detect source language based on script characteristics.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code for detected language
        """
        # Script ranges for Indian languages
        script_ranges = {
            'hin': (0x0900, 0x097F),   # Devanagari
            'ben': (0x0980, 0x09FF),   # Bengali
            'guj': (0x0A80, 0x0AFF),   # Gujarati
            'pan': (0x0A00, 0x0A7F),   # Gurmukhi
            'tel': (0x0C60, 0x0C7F),   # Telugu
            'tam': (0x0B80, 0x0BFF),   # Tamil
            'kan': (0x0C80, 0x0CFF),   # Kannada
            'mal': (0x0D00, 0x0D7F),   # Malayalam
            'mar': (0x0900, 0x097F),   # Marathi (Devanagari)
            'urd': (0x0600, 0x06FF),   # Arabic/Urdu
        }
        
        # Count characters in each script
        script_scores = {lang: 0 for lang in script_ranges}
        
        for char in text:
            char_code = ord(char)
            for lang_code, (start, end) in script_ranges.items():
                if start <= char_code <= end:
                    script_scores[lang_code] += 1
        
        # Return language with highest score
        detected_lang = max(script_scores, key=script_scores.get)
        
        if script_scores[detected_lang] == 0:
            return 'eng'  # Default to English
        
        return detected_lang
    
    def _print_translation_output(
        self,
        original: str,
        translated: str,
        source_lang: str,
        target_lang: str
    ):
        """Print formatted console output for translation."""
        source_name = self.LANGUAGE_CODES.get(source_lang, source_lang)
        target_name = self.LANGUAGE_CODES.get(target_lang, target_lang)
        
        print("\n" + "="*60)
        print(f"Translation: {source_name} → {target_name}")
        print("="*60)
        print(f"Original ({source_name}):")
        print("-"*60)
        print(original)
        print("-"*60)
        print(f"Translated ({target_name}):")
        print("-"*60)
        print(translated)
        print("-"*60 + "\n")
