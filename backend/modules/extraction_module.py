"""
Extraction Module for structured financial field extraction

This module handles:
- Extracting financial fields from normalized text
- Parsing dates, amounts, and identifiers
- Normalizing currency values and standardizing formats
"""

import re
from typing import Dict, Optional, Any, List
from datetime import datetime
import logging
from dataclasses import dataclass, asdict

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@dataclass
class FinancialExtraction:
    """Data class for extracted financial fields"""
    company_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    gst_number: Optional[str] = None
    bank_account: Optional[str] = None
    transaction_amount: Optional[float] = None
    transaction_date: Optional[str] = None
    document_type: Optional[str] = None
    extracted_fields: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extracted_fields is None:
            self.extracted_fields = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class FinancialFieldExtractor:
    """
    Extract structured financial fields from normalized text.
    
    Extracted fields:
    - company_name
    - invoice_number
    - invoice_date
    - total_amount
    - gst_number
    - bank_account
    - transaction_amount
    - transaction_date
    """
    
    # Regex patterns for various fields
    PATTERNS = {
        'invoice_number': [
            r'invoice\s*(?:number|#|no\.?)\s*[:\-]?\s*([A-Z0-9\-/]+)',
            r'inv\s*(?:number|#|no\.?)\s*[:\-]?\s*([A-Z0-9\-/]+)',
            r'(?:ref|reference)\s*(?:number|#|no\.?)\s*[:\-]?\s*([A-Z0-9\-/]+)',
        ],
        'gst_number': [
            r'gst\s*(?:number|#|no\.?|i\.?n\.?)\s*[:\-]?\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9])',
            r'gstin\s*[:\-]?\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9])',
            r'(?:gst|gstin)\s*[:\-]\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9])',
        ],
        'bank_account': [
            r'account\s*(?:number|#|no\.?)\s*[:\-]?\s*([0-9]{10,})',
            r'account[:\-]?\s*([0-9]{10,})',
            r'(?:bank\s*)?account[:\-]?\s*([0-9]{10,})',
        ],
        'amount': [
            r'(?:total|amount|sum|rupees?|₹)\s*[:\-]?\s*([0-9]{1,3}(?:[,][0-9]{3})*(?:\.[0-9]{2})?)',
            r'₹\s*([0-9]{1,3}(?:[,][0-9]{3})*(?:\.[0-9]{2})?)',
            r'rs\.?\s*([0-9]{1,3}(?:[,][0-9]{3})*(?:\.[0-9]{2})?)',
        ],
        'date': [
            r'(?:date|dated|on)\s*[:\-]?\s*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})',
            r'([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})',
            r'(?:date|dated|on)[:\-]\s*([0-9]{1,2}-[0-9]{1,2}-[0-9]{2,4})',
        ],
        'company_name': [
            r'(?:company|firm|business|entity|from)\s*[:\-]?\s*([A-Z][A-Za-z\s&\.]+)',
            r'^([A-Z][A-Za-z\s&\.]+?)(?:\s+(?:limited|ltd|pvt|private|inc|corporation|corp))?[:\-]',
        ]
    }
    
    def __init__(self):
        """Initialize the financial field extractor"""
        self.compiled_patterns = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        for field, patterns in self.PATTERNS.items():
            self.compiled_patterns[field] = [
                re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                for pattern in patterns
            ]
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize extracted text for better field extraction.
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        normalized = text.lower()
        
        # Replace common OCR errors
        normalized = normalized.replace('₹', '₹')
        normalized = normalized.replace('৳', '₹')
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Normalize currency formatting
        normalized = re.sub(r'(\d+)\s*,\s*(\d{2})', r'\1.\2', normalized)
        
        return normalized
    
    def extract_fields(self, text: str) -> FinancialExtraction:
        """
        Extract structured financial fields from text.
        
        Args:
            text: Text to extract fields from
            
        Returns:
            FinancialExtraction object with extracted fields
        """
        # Normalize text
        normalized_text = self.normalize_text(text)
        
        logger.info("Extracting financial fields from text")
        
        result = FinancialExtraction()
        
        # Extract invoice number
        result.invoice_number = self._extract_field(
            normalized_text,
            'invoice_number'
        )
        
        # Extract GST number
        result.gst_number = self._extract_field(
            normalized_text,
            'gst_number'
        )
        
        # Extract bank account
        result.bank_account = self._extract_field(
            normalized_text,
            'bank_account'
        )
        
        # Extract amounts
        amounts = self._extract_all_amounts(normalized_text)
        if amounts:
            result.total_amount = max(amounts)  # Assume largest amount is total
            result.transaction_amount = amounts[0] if amounts else None
        
        # Extract dates
        dates = self._extract_all_dates(normalized_text)
        if dates:
            result.invoice_date = self._standardize_date(dates[0])
            result.transaction_date = self._standardize_date(dates[0])
        
        # Extract company name
        result.company_name = self._extract_field(
            text,  # Use original case for company names
            'company_name'
        )
        
        # Detect document type
        result.document_type = self._detect_document_type(normalized_text)
        
        # Store all extracted fields
        result.extracted_fields = {
            'invoice_number': result.invoice_number,
            'gst_number': result.gst_number,
            'bank_account': result.bank_account,
            'total_amount': result.total_amount,
            'invoice_date': result.invoice_date,
            'transaction_amount': result.transaction_amount,
            'transaction_date': result.transaction_date,
            'company_name': result.company_name,
            'document_type': result.document_type,
        }
        
        # Print extraction results
        self._print_extraction_output(result)
        
        return result
    
    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """
        Extract a single field from text using regex patterns.
        
        Args:
            text: Text to search
            field_name: Name of field to extract
            
        Returns:
            Extracted field value or None
        """
        if field_name not in self.compiled_patterns:
            return None
        
        patterns = self.compiled_patterns[field_name]
        
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                if value:
                    logger.debug(f"Extracted {field_name}: {value}")
                    return value
        
        return None
    
    def _extract_all_amounts(self, text: str) -> List[float]:
        """Extract all amount values from text."""
        amounts = []
        patterns = self.compiled_patterns.get('amount', [])
        
        for pattern in patterns:
            matches = pattern.finditer(text)
            for match in matches:
                amount_str = match.group(1)
                try:
                    # Remove commas and convert to float
                    amount = float(amount_str.replace(',', ''))
                    amounts.append(amount)
                except ValueError:
                    continue
        
        return sorted(set(amounts), reverse=True)
    
    def _extract_all_dates(self, text: str) -> List[str]:
        """Extract all date values from text."""
        dates = []
        patterns = self.compiled_patterns.get('date', [])
        
        for pattern in patterns:
            matches = pattern.finditer(text)
            for match in matches:
                date_str = match.group(1)
                if date_str:
                    dates.append(date_str)
        
        return dates
    
    def _standardize_date(self, date_str: str) -> Optional[str]:
        """
        Standardize date to YYYY-MM-DD format.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Standardized date string or None
        """
        date_formats = [
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%d-%m-%y',
            '%d/%m/%y',
            '%Y-%m-%d',
            '%d %m %Y',
        ]
        
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), date_format)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        logger.warning(f"Could not standardize date: {date_str}")
        return date_str
    
    def _detect_document_type(self, text: str) -> Optional[str]:
        """Detect document type from text content."""
        if 'invoice' in text or 'bill' in text:
            return 'invoice'
        elif 'bank' in text or 'statement' in text or 'account' in text:
            return 'bank_statement'
        elif 'gst' in text or 'filing' in text:
            return 'gst_filing'
        elif 'litigation' in text or 'legal' in text or 'suit' in text:
            return 'legal_notice'
        elif 'annual' in text or 'report' in text:
            return 'annual_report'
        else:
            return 'unknown'
    
    def _print_extraction_output(self, result: FinancialExtraction):
        """Print formatted console output for extracted data."""
        print("\n" + "="*60)
        print("Extracted Structured Data")
        print("="*60)
        
        extracted_dict = {
            k: v for k, v in result.to_dict().items()
            if k != 'extracted_fields' and v is not None
        }
        
        for key, value in extracted_dict.items():
            if value is not None:
                print(f"{key}: {value}")
        
        print("-"*60 + "\n")
