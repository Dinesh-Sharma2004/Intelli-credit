"""
Multilingual Document Processing Modules
Includes OCR, Translation, Extraction, Database, and Evaluation modules
"""

from .ocr_module import IndicTrOCR
from .translation_module import IndicTranslator
from .extraction_module import FinancialFieldExtractor
from .database_module import DatabaseManager
from .evaluation_module import OCREvaluator

__all__ = [
    "IndicTrOCR",
    "IndicTranslator",
    "FinancialFieldExtractor",
    "DatabaseManager",
    "OCREvaluator",
]
