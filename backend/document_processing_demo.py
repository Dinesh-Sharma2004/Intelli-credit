#!/usr/bin/env python3
"""
Demonstration script for using the Integrated Document Processing Pipeline

This script shows three approaches:
1. Direct Python API (programmatic)
2. REST API via HTTP requests
3. Batch processing
"""

import json
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
UPLOAD_DIR = "backend/uploads"
RESULTS_DIR = "backend/processed_documents"


class DocumentProcessingDemo:
    """Demonstration of document processing pipeline usage."""

    def __init__(self, api_url: str = API_BASE_URL):
        """Initialize demo with API endpoint."""
        self.api_url = api_url
        self.session = requests.Session()

    # ==================== REST API Approach ====================

    def api_upload_and_process(self, file_path: str, language: str = "hindi") -> Dict:
        """
        Upload and process document via REST API.

        Args:
            file_path: Path to PDF file
            language: Document language (hindi, tamil, telugu, etc.)

        Returns:
            Processing result dictionary
        """
        print(f"\n📤 Uploading document: {file_path}")
        print(f"Language: {language}")

        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"language": language}

            try:
                response = self.session.post(
                    f"{self.api_url}/documents/upload", files=files, data=data
                )
                response.raise_for_status()
                result = response.json()

                if result.get("success"):
                    document_id = result["data"]["document_id"]
                    print(f"✅ Document uploaded successfully")
                    print(f"   Document ID: {document_id}")
                    print(f"   Pages processed: {result['data']['pages_processed']}")
                    return result["data"]
                else:
                    print(f"❌ Upload failed: {result.get('error')}")
                    return None

            except requests.exceptions.RequestException as e:
                print(f"❌ Connection error: {e}")
                return None

    def api_list_documents(self, limit: int = 10, skip: int = 0) -> List[Dict]:
        """
        List processed documents via API.

        Args:
            limit: Number of documents to retrieve
            skip: Number of documents to skip

        Returns:
            List of document records
        """
        print(f"\n📋 Fetching {limit} documents...")

        try:
            response = self.session.get(
                f"{self.api_url}/documents/list", params={"skip": skip, "limit": limit}
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                documents = result["data"]
                print(f"✅ Found {len(documents)} documents")
                return documents
            else:
                print(f"❌ Failed to fetch: {result.get('error')}")
                return []

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return []

    def api_search_documents(
        self,
        document_type: Optional[str] = None,
        language: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search documents with filters via API.

        Args:
            document_type: Type of document (invoice, bank_statement, etc.)
            language: Original document language
            start_date: Earliest date to include
            end_date: Latest date to include

        Returns:
            List of matching documents
        """
        print(f"\n🔍 Searching documents...")

        search_params = {}
        if document_type:
            search_params["document_type"] = document_type
            print(f"   Type: {document_type}")
        if language:
            search_params["language"] = language
            print(f"   Language: {language}")
        if start_date:
            search_params["start_date"] = start_date
            print(f"   From: {start_date}")
        if end_date:
            search_params["end_date"] = end_date
            print(f"   To: {end_date}")

        try:
            response = self.session.post(
                f"{self.api_url}/documents/search", json=search_params
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                documents = result["data"]
                print(f"✅ Found {len(documents)} matching documents")
                return documents
            else:
                print(f"❌ Search failed: {result.get('error')}")
                return []

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return []

    def api_get_document(self, document_id: str) -> Dict:
        """
        Get document details via API.

        Args:
            document_id: UUID of the document

        Returns:
            Document details dictionary
        """
        print(f"\n📄 Fetching document: {document_id}")

        try:
            response = self.session.get(f"{self.api_url}/documents/{document_id}")
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                document = result["data"]
                print(f"✅ Document retrieved")
                print(f"   File: {document.get('file_name')}")
                print(f"   Language: {document.get('original_language')}")
                print(f"   Type: {document.get('document_type')}")
                print(f"   Pages: {len(document.get('pages', []))}")
                return document
            else:
                print(f"❌ Fetch failed: {result.get('error')}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return None

    def api_batch_process(self, file_paths: List[str], language: str = "hindi") -> Dict:
        """
        Process multiple documents in batch via API.

        Args:
            file_paths: List of PDF file paths
            language: Document language

        Returns:
            Batch processing result
        """
        print(f"\n⚙️  Starting batch process for {len(file_paths)} files...")

        try:
            response = self.session.post(
                f"{self.api_url}/documents/batch-process",
                json={"file_paths": file_paths, "language": language},
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                data = result["data"]
                print(f"✅ Batch processing completed")
                print(f"   Successful: {data['successful_count']}")
                print(f"   Failed: {data['failed_count']}")
                return data
            else:
                print(f"❌ Batch failed: {result.get('error')}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return None

    def api_check_status(self) -> Dict:
        """Check model and system status via API."""
        print(f"\n🔍 Checking system status...")

        try:
            response = self.session.get(f"{self.api_url}/status/models")
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                status = result["data"]
                print(f"✅ System status:")
                print(f"   OCR Model: {'✓ Available' if status['ocr_model_available'] else '✗ Missing'}")
                print(f"   Translation: {'✓ Available' if status['translation_model_available'] else '✗ Missing'}")
                print(f"   Database: {'✓ Connected' if status['database_connected'] else '✗ Not connected'}")
                return status
            else:
                print(f"❌ Status check failed: {result.get('error')}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            print(f"   Make sure API server is running: python -m uvicorn backend.document_processing_api:app")
            return None

    # ==================== Direct Python API Approach ====================

    def python_process_document(self, file_path: str):
        """
        Example of using the integrated pipeline directly via Python.

        This requires importing the modules:
        from integrated_document_pipeline import IntegratedDocumentPipeline
        from modules import IndicTrOCR, IndicTranslator
        """
        print(f"\n🐍 Python API Example (direct usage):")
        print(f"   File: {file_path}")

        example_code = """
from integrated_document_pipeline import IntegratedDocumentPipeline

# Initialize components (models must be downloaded first)
pipeline = IntegratedDocumentPipeline(
    ocr_model=None,  # Auto-load if available
    translator=None,  # Auto-load if available
    extractor=None,   # Auto-load if available
    db_manager=None   # Auto-load if available
)

# Process document
result = pipeline.process_pdf_document('{pdf_path}', language='hindi')

# Results structure
document_id = result['document_id']
pages_count = len(result['pages'])
translations = result['translations']

# Access extracted fields
for page in translations:
    fields = page.get('extracted_fields', {})
    print(f"Page {page['page_number']}:")
    print(f"  Company: {fields.get('company_name')}")
    print(f"  Amount: {fields.get('total_amount')}")
    print(f"  GST: {fields.get('gst_number')}")

# Save report
report = pipeline.get_processing_report(document_id)
with open(f'report_{document_id}.json', 'w') as f:
    json.dump(report, f, indent=2)
        """.format(
            pdf_path=file_path
        )

        print(example_code)

    # ==================== Workflow Examples ====================

    def example_single_document_workflow(self, pdf_file: str):
        """Complete workflow for processing a single document."""
        print("\n" + "=" * 60)
        print("EXAMPLE 1: Single Document Processing Workflow")
        print("=" * 60)

        # Step 1: Check system status
        status = self.api_check_status()
        if not status:
            print("⚠️  System not ready. Ensure API server is running.")
            return

        # Step 2: Upload and process
        result = self.api_upload_and_process(pdf_file, language="hindi")
        if not result:
            return

        document_id = result["document_id"]

        # Step 3: Poll for completion
        print(f"\n⏳ Waiting for processing...")
        for i in range(5):
            time.sleep(2)
            doc = self.api_get_document(document_id)
            if doc and doc.get("overall_status") == "completed":
                print(f"✅ Processing completed!")
                break
            else:
                print(f"   Status: {doc.get('overall_status') if doc else 'Unknown'}")

        # Step 4: Display results
        if doc:
            print(f"\n📊 Processing Summary:")
            print(f"   Pages: {len(doc.get('pages', []))}")
            print(f"   Language: {doc.get('original_language')}")
            if doc.get("pages"):
                first_page = doc["pages"][0]
                print(f"   First page preview: {first_page[:100]}...")

    def example_batch_processing_workflow(self, pdf_files: List[str]):
        """Workflow for batch processing multiple documents."""
        print("\n" + "=" * 60)
        print("EXAMPLE 2: Batch Processing Workflow")
        print("=" * 60)

        if not pdf_files:
            print("No PDF files provided")
            return

        # Step 1: Verify files exist
        valid_files = []
        for f in pdf_files:
            if Path(f).exists():
                valid_files.append(f)
            else:
                print(f"⚠️  File not found: {f}")

        if not valid_files:
            return

        # Step 2: Process batch
        result = self.api_batch_process(valid_files, language="hindi")

        # Step 3: List processed documents
        if result and result["successful_count"] > 0:
            print(f"\n📋 Listing all documents...")
            documents = self.api_list_documents(limit=10)

            if documents:
                print(f"\nFirst document summary:")
                doc = documents[0]
                print(f"  ID: {doc.get('document_id')}")
                print(f"  File: {doc.get('file_name')}")
                print(f"  Status: {doc.get('overall_status')}")

    def example_search_and_filter(self):
        """Workflow for searching and filtering documents."""
        print("\n" + "=" * 60)
        print("EXAMPLE 3: Search and Filter Workflow")
        print("=" * 60)

        # Search invoices in Hindi
        invoices = self.api_search_documents(document_type="invoice", language="hindi")

        if invoices:
            print(f"\n📋 Found {len(invoices)} Hindi invoices")
            for i, doc in enumerate(invoices[:3], 1):
                print(f"\n  {i}. {doc.get('file_name')}")
                print(f"     Created: {doc.get('created_at')}")
                print(f"     Status: {doc.get('overall_status')}")

    # ==================== Utility Methods ====================

    def display_extracted_fields(self, document_id: str):
        """Display all extracted fields from a document."""
        print(f"\n" + "=" * 60)
        print(f"Extracted Fields for {document_id}")
        print("=" * 60)

        doc = self.api_get_document(document_id)
        if not doc:
            return

        # Display extracted data
        for i, page in enumerate(doc.get("pages", []), 1):
            print(f"\nPage {i}:")
            fields = page.get("extracted_fields", {})
            for key, value in fields.items():
                if key != "raw_content":
                    print(f"  {key}: {value}")


# ==================== Main Execution ====================


def main():
    """Main execution with examples."""
    print("=" * 60)
    print("Document Processing Pipeline - Usage Examples")
    print("=" * 60)

    demo = DocumentProcessingDemo()

    # Example 1: Check API health
    print("\n[1] Checking API health...")
    demo.api_check_status()

    # Example 2: Single document processing
    print("\n[2] Single document workflow:")
    print("   Usage: demo.example_single_document_workflow('path/to/file.pdf')")
    # demo.example_single_document_workflow('backend/data/sample_invoice.pdf')

    # Example 3: Batch processing
    print("\n[3] Batch processing workflow:")
    print("   Usage: demo.example_batch_processing_workflow(['file1.pdf', 'file2.pdf'])")
    # demo.example_batch_processing_workflow(['file1.pdf', 'file2.pdf'])

    # Example 4: Search and filter
    print("\n[4] Search and filter workflow:")
    print("   Usage: demo.example_search_and_filter()")
    # demo.example_search_and_filter()

    # Example 5: Direct Python usage
    print("\n[5] Direct Python API usage:")
    demo.python_process_document("path/to/document.pdf")

    # Example 6: Complete example
    print("\n" + "=" * 60)
    print("Complete Usage Example")
    print("=" * 60)

    example_script = """
from document_processing_demo import DocumentProcessingDemo

# Initialize
demo = DocumentProcessingDemo()

# 1. Check system
demo.api_check_status()

# 2. Process one document
result = demo.api_upload_and_process('invoice.pdf', language='hindi')
document_id = result['document_id']

# 3. View results
doc = demo.api_get_document(document_id)
demo.display_extracted_fields(document_id)

# 4. Search documents
invoices = demo.api_search_documents(
    document_type='invoice',
    language='hindi'
)

# 5. Batch process
results = demo.api_batch_process(['file1.pdf', 'file2.pdf'])
    """

    print(example_script)

    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Start API server: uvicorn backend.document_processing_api:app")
    print("2. Run this demo: python document_processing_demo.py")
    print("3. Check /api/v1/docs for full API documentation")
    print("4. Fine-tune translation: python backend/prepare_finetuning.py")


if __name__ == "__main__":
    main()
