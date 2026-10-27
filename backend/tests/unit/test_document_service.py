import json
from io import BytesIO
from pathlib import Path

import pytest
from werkzeug.datastructures import FileStorage

from app.services.document_catalog import classify_document
from app.services.document_service import DocumentProcessingService, UnsupportedDocumentError
from app.services.ocr_service import OCRService

ALLOWED = {".pdf", ".csv", ".json", ".txt", ".png"}


@pytest.fixture
def service(tmp_path):
    return DocumentProcessingService(tmp_path / "uploads", workers=2, ocr_service=OCRService(), allowed_extensions=ALLOWED)


def write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "filename, doc_type",
    [
        ("FY24 Annual Report.pdf", "annual_report"),
        ("gstr-returns-fy24.csv", "gst_filing"),
        ("bank-statement-apr.csv", "bank_statement"),
        ("crisil-rating-letter.pdf", "rating_report"),
        ("random.pdf", "generic_pdf"),
    ],
)
def test_classification_by_filename(filename, doc_type):
    assert classify_document(filename).document_type == doc_type


def test_gst_csv_is_parsed_into_structured_returns(tmp_path, service):
    path = write(tmp_path, "gstr-returns.csv",
                 "period,gstr1_taxable_value,gstr3b_taxable_value,itc_available_2b,itc_claimed_3b\n"
                 "2023-04,100,95,10,12\n2023-05,110,110,11,11\n")
    parsed = service.parse_structured_records(path)
    assert [row["period"] for row in parsed["gst_returns"]] == ["2023-04", "2023-05"]
    assert "bank_transactions" not in parsed


def test_bank_csv_with_bom_and_mixed_case_headers(tmp_path, service):
    path = tmp_path / "bank-statement.csv"
    path.write_bytes("﻿Date,Description,Counterparty,Debit,Credit\n2024-01-10,NEFT,Acme,,500\n".encode("utf-8"))
    parsed = service.parse_structured_records(path)
    assert parsed["bank_transactions"][0]["credit"] == "500"


def test_json_payloads_and_unrelated_tables(tmp_path, service):
    json_path = write(tmp_path, "records.json", json.dumps({"gst_returns": [{"period": "2023-04"}], "bank_transactions": []}))
    assert set(service.parse_structured_records(json_path)) == {"gst_returns", "bank_transactions"}
    other = write(tmp_path, "inventory.csv", "sku,qty\nA,1\n")
    assert service.parse_structured_records(other) == {}
    broken = write(tmp_path, "broken.json", "{not json")
    assert service.parse_structured_records(broken) == {}


@pytest.mark.parametrize("name", ["malware.exe", "script.sh", "noextension", ""])
def test_disallowed_uploads_are_rejected(service, name):
    with pytest.raises(UnsupportedDocumentError):
        service.validate_filename(name)


def test_uploaded_filenames_cannot_escape_upload_dir(tmp_path, service):
    upload = FileStorage(stream=BytesIO(b"hello"), filename="../../outside/annual-report.txt")
    saved = service.persist_documents([upload])[0]
    assert saved.parent == service.upload_dir
    assert saved.name.endswith("_annual-report.txt")
    assert not (tmp_path / "outside").exists()


def test_text_document_gets_entities_and_flags(tmp_path, service):
    path = write(tmp_path, "annual-report.txt",
                 "Acme Foods Private Limited GSTIN 27AAPFU0939F1ZV PAN AAPFU0939F. Revenue Rs. 120 crore. "
                 "The auditor issued a qualified opinion and noted litigation with a supplier.")
    doc = service.process_single_document(path)
    facts = doc["structured_data"]
    assert doc["document_type"] == "annual_report" and doc["processing_status"] == "completed"
    assert facts["gstin"] == "27AAPFU0939F1ZV" and facts["pan"] == "AAPFU0939F"
    assert 1_200_000_000 in facts["monetary_amounts_inr"]
    assert "Auditor qualification detected" in doc["risk_flags"]
    assert "Litigation-related terminology detected" in doc["risk_flags"]


def test_processing_is_cached_by_content_version(tmp_path, service):
    path = write(tmp_path, "notes.txt", "first version")
    first = service.process_single_document(path)
    assert service.process_single_document(path) == first
    path.write_text("second version with more text", encoding="utf-8")
    assert service.process_single_document(path)["extracted_text"] == "second version with more text"


def test_corrupt_pdf_is_reported_as_failed(tmp_path, service):
    path = tmp_path / "annual-report.pdf"
    path.write_bytes(b"%PDF-1.4 this is not really a pdf")
    doc = service.process_single_document(path)
    assert doc["processing_status"] in {"failed", "needs_review"}
    assert doc["confidence_score"] <= 0.5


@pytest.mark.ocr
def test_scanned_rating_report_goes_through_ocr(service, synthetic_data, requires_ocr):
    info = synthetic_data["borrowers"]["sunrise-agro"]
    doc = service.process_single_document(Path(info["files"]["rating_report"]))
    assert doc["metadata_json"]["extraction_source"] == "ocr"
    assert doc["metadata_json"]["ocr_engine"] == "rapidocr"
    assert doc["structured_data"]["gstin"] == info["application"]["borrower_gstin"]   # OCR misreads repaired
    assert doc["structured_data"]["credit_ratings"] == ["A-"]


def test_parallel_processing_preserves_order(tmp_path, service):
    paths = [write(tmp_path, f"doc-{i}.txt", f"document number {i}") for i in range(6)]
    results = service.process_documents_parallel(paths)
    assert [r["extracted_text"] for r in results] == [f"document number {i}" for i in range(6)]
