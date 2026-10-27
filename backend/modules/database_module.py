"""
Database Module for PostgreSQL integration

This module handles:
- Database connection and management
- Creating and managing extracted_financial_documents table
- Storing OCR results, translations, and extracted fields
- CRUD operations for financial documents
"""

import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, Column, String, Text, Float, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

Base = declarative_base()


class ExtractedFinancialDocument(Base):
    """SQLAlchemy model for extracted financial documents"""
    
    __tablename__ = 'extracted_financial_documents'
    
    document_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    original_language_text = Column(Text, nullable=True)
    translated_english_text = Column(Text, nullable=True)
    invoice_number = Column(String(255), nullable=True)
    invoice_date = Column(Date, nullable=True)
    total_amount = Column(Float, nullable=True)
    gst_number = Column(String(15), nullable=True)
    bank_account = Column(String(255), nullable=True)
    transaction_amount = Column(Float, nullable=True)
    transaction_date = Column(Date, nullable=True)
    company_name = Column(String(255), nullable=True)
    document_type = Column(String(50), nullable=True)
    source_image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy serialization"""
        return {
            'document_id': str(self.document_id),
            'original_language_text': self.original_language_text,
            'translated_english_text': self.translated_english_text,
            'invoice_number': self.invoice_number,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'total_amount': self.total_amount,
            'gst_number': self.gst_number,
            'bank_account': self.bank_account,
            'transaction_amount': self.transaction_amount,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'company_name': self.company_name,
            'document_type': self.document_type,
            'source_image_path': self.source_image_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class DatabaseManager:
    """
    Manage PostgreSQL database operations for financial documents.
    
    Configuration:
    - PostgreSQL connection string via environment variable DATABASE_URL
    - Or default to: postgresql://user:password@localhost:5432/intelli_credit
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        echo: bool = False
    ):
        """
        Initialize database manager.
        
        Args:
            database_url: PostgreSQL connection string
            echo: Whether to echo SQL queries
        """
        if database_url is None:
            database_url = self._get_default_database_url()
        
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        
        self._initialize_database(echo)
    
    def _get_default_database_url(self) -> str:
        """Get default database URL from environment or use default"""
        import os
        
        db_url = os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:password@localhost:5432/intelli_credit'
        )
        
        return db_url
    
    def _initialize_database(self, echo: bool = False):
        """Initialize database engine and session factory"""
        try:
            logger.info(f"Connecting to database: {self._mask_credentials(self.database_url)}")
            
            self.engine = create_engine(
                self.database_url,
                echo=echo,
                future=True,
                pool_pre_ping=True,  # Verify connections before using
                connect_args={'check_same_thread': False} if 'sqlite' in self.database_url else {}
            )
            
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                expire_on_commit=False,
                future=True
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            
            logger.info("Database connection successful")
            
            # Create tables
            self.create_tables()
            
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            logger.info("Make sure PostgreSQL is running and DATABASE_URL is correct")
            raise
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    def insert_document(
        self,
        original_text: str,
        translated_text: str,
        extracted_data: Dict[str, Any],
        source_image_path: Optional[str] = None
    ) -> str:
        """
        Insert extracted financial document into database.
        
        Args:
            original_text: Original OCR text
            translated_text: Translated English text
            extracted_data: Dictionary of extracted fields
            source_image_path: Path to source image
            
        Returns:
            Document ID (UUID)
        """
        session = self.get_session()
        
        try:
            # Parse date strings to date objects
            invoice_date = None
            transaction_date = None
            
            if extracted_data.get('invoice_date'):
                try:
                    from datetime import datetime
                    invoice_date = datetime.strptime(
                        extracted_data['invoice_date'],
                        '%Y-%m-%d'
                    ).date()
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse invoice_date: {extracted_data.get('invoice_date')}")
            
            if extracted_data.get('transaction_date'):
                try:
                    from datetime import datetime
                    transaction_date = datetime.strptime(
                        extracted_data['transaction_date'],
                        '%Y-%m-%d'
                    ).date()
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse transaction_date: {extracted_data.get('transaction_date')}")
            
            # Create document record
            document = ExtractedFinancialDocument(
                original_language_text=original_text,
                translated_english_text=translated_text,
                invoice_number=extracted_data.get('invoice_number'),
                invoice_date=invoice_date,
                total_amount=extracted_data.get('total_amount'),
                gst_number=extracted_data.get('gst_number'),
                bank_account=extracted_data.get('bank_account'),
                transaction_amount=extracted_data.get('transaction_amount'),
                transaction_date=transaction_date,
                company_name=extracted_data.get('company_name'),
                document_type=extracted_data.get('document_type'),
                source_image_path=source_image_path
            )
            
            session.add(document)
            session.commit()
            
            document_id = str(document.document_id)
            logger.info(f"Document inserted successfully with ID: {document_id}")
            
            # Print database confirmation
            self._print_database_confirmation(document)
            
            return document_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting document: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document by ID.
        
        Args:
            document_id: UUID of document
            
        Returns:
            Document dictionary or None if not found
        """
        session = self.get_session()
        
        try:
            document = session.query(ExtractedFinancialDocument).filter(
                ExtractedFinancialDocument.document_id == uuid.UUID(document_id)
            ).first()
            
            if document:
                return document.to_dict()
            return None
        finally:
            session.close()
    
    def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve all documents with pagination.
        
        Args:
            limit: Number of documents to retrieve
            offset: Number of documents to skip
            
        Returns:
            List of document dictionaries
        """
        session = self.get_session()
        
        try:
            documents = session.query(ExtractedFinancialDocument).limit(
                limit
            ).offset(offset).all()
            
            return [doc.to_dict() for doc in documents]
        finally:
            session.close()
    
    def search_documents(self, **filters) -> List[Dict[str, Any]]:
        """
        Search documents by field values.
        
        Args:
            **filters: Field filters (e.g., gst_number='...', invoice_date='...')
            
        Returns:
            List of matching documents
        """
        session = self.get_session()
        
        try:
            query = session.query(ExtractedFinancialDocument)
            
            for field, value in filters.items():
                if hasattr(ExtractedFinancialDocument, field):
                    query = query.filter(
                        getattr(ExtractedFinancialDocument, field) == value
                    )
            
            documents = query.all()
            return [doc.to_dict() for doc in documents]
        finally:
            session.close()
    
    def update_document(
        self,
        document_id: str,
        **updates
    ) -> Optional[Dict[str, Any]]:
        """
        Update document fields.
        
        Args:
            document_id: UUID of document
            **updates: Fields to update
            
        Returns:
            Updated document dictionary or None
        """
        session = self.get_session()
        
        try:
            document = session.query(ExtractedFinancialDocument).filter(
                ExtractedFinancialDocument.document_id == uuid.UUID(document_id)
            ).first()
            
            if not document:
                return None
            
            for field, value in updates.items():
                if hasattr(document, field):
                    setattr(document, field, value)
            
            document.updated_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"Document {document_id} updated successfully")
            return document.to_dict()
        finally:
            session.close()
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete document by ID.
        
        Args:
            document_id: UUID of document
            
        Returns:
            True if deleted, False if not found
        """
        session = self.get_session()
        
        try:
            document = session.query(ExtractedFinancialDocument).filter(
                ExtractedFinancialDocument.document_id == uuid.UUID(document_id)
            ).first()
            
            if not document:
                return False
            
            session.delete(document)
            session.commit()
            
            logger.info(f"Document {document_id} deleted successfully")
            return True
        finally:
            session.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        session = self.get_session()
        
        try:
            total_count = session.query(ExtractedFinancialDocument).count()
            
            # Count by document type
            from sqlalchemy import func
            type_counts = session.query(
                ExtractedFinancialDocument.document_type,
                func.count(ExtractedFinancialDocument.document_id)
            ).group_by(ExtractedFinancialDocument.document_type).all()
            
            stats = {
                'total_documents': total_count,
                'documents_by_type': {
                    dtype: count for dtype, count in type_counts
                },
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return stats
        finally:
            session.close()
    
    def _mask_credentials(self, url: str) -> str:
        """Mask credentials in database URL for logging"""
        import re
        return re.sub(
            r'(\w+):[^@]+@',
            r'\1:****@',
            url
        )
    
    def _print_database_confirmation(self, document: ExtractedFinancialDocument):
        """Print formatted console output for database insertion"""
        print("\n" + "="*60)
        print("Database Insertion Confirmation")
        print("="*60)
        print(f"Document ID: {document.document_id}")
        print(f"Invoice Number: {document.invoice_number}")
        print(f"Invoice Date: {document.invoice_date}")
        print(f"Total Amount: ₹{document.total_amount:,.2f}" if document.total_amount else "Total Amount: N/A")
        print(f"Company Name: {document.company_name}")
        print(f"Document Type: {document.document_type}")
        print(f"Created At: {document.created_at}")
        print("-"*60 + "\n")
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
