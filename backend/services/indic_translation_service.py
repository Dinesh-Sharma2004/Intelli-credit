"""
IndicTrans2 Integration Service
Translates extracted text from Indian languages to other Indian languages or English
"""

import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import torch

logger = logging.getLogger(__name__)

# Try to import IndicTrans2
try:
    from ai4bharat.transliteration import XlitEngine  # For transliteration
    TRANSLITERATION_AVAILABLE = True
except ImportError:
    TRANSLITERATION_AVAILABLE = False
    logger.info("ai4bharat transliteration not available, will install from source")

try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.error("Transformers not installed")


class IndicTranslationService:
    """
    Translation Service using IndicTrans2
    Supports translation between Indian languages and English
    """
    
    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or Path(__file__).parent.parent / "models" / "indictrans2"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.models = {}  # Cache for loaded models
        self.tokenizers = {}
        
        # Language codes supported by IndicTrans2
        self.supported_languages = {
            'as': 'Assamese',
            'bn': 'Bengali',
            'gu': 'Gujarati',
            'hi': 'Hindi',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'mr': 'Marathi',
            'or': 'Odia',
            'pa': 'Punjabi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'ur': 'Urdu',
            'en': 'English'
        }
        
        # Reverse mapping for language name to code
        self.lang_name_to_code = {v.lower(): k for k, v in self.supported_languages.items()}
        
        logger.info(f"IndicTrans2 Service initialized. Device: {self.device}")
    
    def get_model_id(self, source_lang: str, target_lang: str) -> str:
        """
        Get the appropriate IndicTrans2 model identifier
        Format: ai4bharat/indic-trans-v2_{source}_{target}
        """
        # Normalize language codes
        src = self._normalize_language_code(source_lang)
        tgt = self._normalize_language_code(target_lang)
        
        # IndicTrans2 model naming convention
        if src == 'en':
            return f"ai4bharat/indic-trans-v2_en_{tgt}"
        elif tgt == 'en':
            return f"ai4bharat/indic-trans-v2_{src}_en"
        else:
            return f"ai4bharat/indic-trans-v2_{src}_{tgt}"
    
    def _normalize_language_code(self, lang: str) -> str:
        """Normalize language input to code"""
        lang_lower = lang.lower()
        
        # If already a code
        if lang_lower in self.supported_languages:
            return lang_lower
        
        # If a name
        if lang_lower in self.lang_name_to_code:
            return self.lang_name_to_code[lang_lower]
        
        # Default to Hindi if not found
        logger.warning(f"Language {lang} not supported, defaulting to Hindi")
        return 'hi'
    
    def load_model(self, source_lang: str, target_lang: str):
        """Load translation model for language pair"""
        src = self._normalize_language_code(source_lang)
        tgt = self._normalize_language_code(target_lang)
        
        model_key = f"{src}_{tgt}"
        
        if model_key in self.models:
            return self.models[model_key], self.tokenizers[model_key]
        
        model_id = self.get_model_id(src, tgt)
        
        try:
            logger.info(f"Loading translation model: {model_id}")
            
            # Load model
            model = AutoModelForSeq2SeqLM.from_pretrained(model_id, trust_remote_code=True)
            model = model.to(self.device)
            model.eval()
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            
            # Cache
            self.models[model_key] = model
            self.tokenizers[model_key] = tokenizer
            
            logger.info(f"Translation model loaded: {src} -> {tgt}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Error loading translation model {model_id}: {e}")
            raise
    
    def translate(self, text: str, source_lang: str = 'hindi', target_lang: str = 'english') -> Dict:
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_lang: Source language (code or name)
            target_lang: Target language (code or name)
        
        Returns:
            Dict with keys: original_text, translated_text, confidence, language_from, language_to, processing_time
        """
        try:
            if not text or not text.strip():
                return {
                    'original_text': text,
                    'translated_text': text,
                    'confidence': 1.0,
                    'language_from': source_lang,
                    'language_to': target_lang,
                    'processing_time': 0,
                    'word_count': 0
                }
            
            start_time = datetime.utcnow()
            
            src = self._normalize_language_code(source_lang)
            tgt = self._normalize_language_code(target_lang)
            
            # Load model
            model, tokenizer = self.load_model(src, tgt)
            
            # Add language token
            input_text = f"<{tgt}> {text}"
            
            # Tokenize
            inputs = tokenizer(input_text, return_tensors="pt", padding=True, truncation=True).to(self.device)
            
            # Generate translation
            with torch.no_grad():
                outputs = model.generate(**inputs, max_length=200)
            
            # Decode
            translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove language token if present
            translated_text = translated_text.replace(f"<{tgt}>", "").strip()
            
            # Calculate confidence
            confidence = self.calculate_translation_confidence(
                text, translated_text, src, tgt
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                'original_text': text,
                'translated_text': translated_text,
                'confidence': confidence,
                'language_from': src,
                'language_to': tgt,
                'processing_time': processing_time,
                'character_count': len(translated_text),
                'word_count': len(translated_text.split())
            }
            
            logger.info(f"Translation completed: {src} -> {tgt}, confidence: {confidence:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            # Return original text if translation fails
            return {
                'original_text': text,
                'translated_text': text,
                'confidence': 0.5,
                'language_from': source_lang,
                'language_to': target_lang,
                'processing_time': 0,
                'error': str(e),
                'word_count': len(text.split())
            }
    
    def translate_batch(self, texts: List[str], source_lang: str = 'hindi', 
                       target_lang: str = 'english') -> List[Dict]:
        """Translate multiple texts at once"""
        results = []
        for text in texts:
            result = self.translate(text, source_lang, target_lang)
            results.append(result)
        return results
    
    def calculate_translation_confidence(self, original: str, translated: str, 
                                        src_lang: str, tgt_lang: str) -> float:
        """
        Calculate confidence score for translation
        Based on text length preservation, complexity, and language pair
        """
        # Base confidence
        confidence = 0.75
        
        # Adjust based on text length
        src_words = len(original.split())
        tgt_words = len(translated.split())
        
        if src_words > 0:
            ratio = tgt_words / src_words
            # Typical translation ratio is 0.8-1.2
            if 0.7 < ratio < 1.3:
                confidence += 0.15
            else:
                confidence -= 0.1
        
        # High confidence for common language pairs
        common_pairs = [
            ('hi', 'en'), ('hi', 'ta'), ('hi', 'te'),
            ('ta', 'en'), ('te', 'en'), ('kn', 'en'),
            ('ml', 'en'), ('bn', 'en'), ('gu', 'en')
        ]
        
        if (src_lang, tgt_lang) in common_pairs:
            confidence += 0.05
        
        return min(0.99, max(0.5, confidence))
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Return supported languages"""
        return self.supported_languages.copy()


# Singleton instance
_translation_service = None

def get_translation_service() -> IndicTranslationService:
    """Get or create translation service singleton"""
    global _translation_service
    if _translation_service is None:
        _translation_service = IndicTranslationService()
    return _translation_service
