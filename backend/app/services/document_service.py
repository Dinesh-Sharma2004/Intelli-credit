from __future__ import annotations

import csv
import io
import json
import re
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Any

from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

from .document_catalog import classify_document
from .ner_service import FinancialNERService
from .ocr_service import IMAGE_SUFFIXES, OCRService


GST_RETURN_COLUMNS = {"period", "gstr1_taxable_value", "gstr3b_taxable_value"}
BANK_COLUMNS = {"date", "debit", "credit"}


class UnsupportedDocumentError(ValueError):
    """Raised when an upload has a file type the pipeline does not accept."""


class DocumentProcessingService:
    def __init__(
        self,
        upload_dir: Path,
        workers: int = 4,
        ocr_service: OCRService | None = None,
        ocr_confidence_threshold: float = 0.55,
        enable_ocr_fallback: bool = True,
        demo_mode: bool = True,
        ner_service: FinancialNERService | None = None,
        allowed_extensions: set[str] | None = None,
    ):
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.workers = workers
        self.ocr_service = ocr_service or OCRService()
        self.ocr_confidence_threshold = ocr_confidence_threshold
        self.enable_ocr_fallback = enable_ocr_fallback
        self.demo_mode = demo_mode
        self.ner_service = ner_service or FinancialNERService()
        self.allowed_extensions = {ext.lower() for ext in (allowed_extensions or set())}
        self._cache: dict[str, dict] = {}
        self._cache_lock = Lock()

    def validate_filename(self, filename: str) -> str:
        name = Path(str(filename or "")).name
        if not name:
            raise UnsupportedDocumentError("Uploaded file has no name")
        suffix = Path(name).suffix.lower()
        if self.allowed_extensions and suffix not in self.allowed_extensions:
            raise UnsupportedDocumentError(f"Unsupported file type '{suffix or name}'")
        return name

    def persist_documents(self, files: list[Any]) -> list[Path]:
        names = [self.validate_filename(uploaded.filename) for uploaded in files]
        saved_paths: list[Path] = []
        for uploaded, original_name in zip(files, names):
            target = self.upload_dir / f"{uuid.uuid4()}_{original_name}"
            uploaded.save(target)
            saved_paths.append(target)
        return saved_paths

    def import_existing_paths(self, filepaths: list[str]) -> list[Path]:
        saved_paths: list[Path] = []
        for file_path in filepaths:
            source = Path(file_path)
            if not source.exists():
                raise FileNotFoundError(f"Document not found: {source}")
            self.validate_filename(source.name)
            target = self.upload_dir / f"{uuid.uuid4()}_{source.name}"
            shutil.copy2(source, target)
            saved_paths.append(target)
        return saved_paths

    def process_documents_parallel(self, paths: list[Path]) -> list[dict]:
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            return list(executor.map(self.process_single_document, paths))

    def process_single_document(self, path: Path) -> dict:
        cache_key = f"{path.resolve()}::{path.stat().st_mtime_ns}::{path.stat().st_size}"
        with self._cache_lock:
            cached = self._cache.get(cache_key)
        if cached is not None:
            return dict(cached)

        try:
            rule = classify_document(path.name)
            suffix = path.suffix.lower()
            text = self.extract_text(path)
            native_confidence = self.estimate_native_confidence(text)
            extraction_source = "native"
            ocr_payload = {"engine": None, "page_confidences": [], "ocr_confidence": native_confidence, "tables": [], "bounding_boxes": []}
            if self.enable_ocr_fallback and suffix in IMAGE_SUFFIXES:
                ocr_payload = self.ocr_service.extract_image(path)
                text = ocr_payload["text"]
                extraction_source = "ocr" if text else "failed"
            elif self.enable_ocr_fallback and suffix == ".pdf" and native_confidence < self.ocr_confidence_threshold:
                ocr_payload = self.ocr_service.extract_pdf(path, native_text=text)
                if ocr_payload["text"] and ocr_payload["ocr_confidence"] >= native_confidence:
                    text = ocr_payload["text"]
                    extraction_source = "ocr"

            facts = self.extract_financial_facts(text, path.name)
            facts.update(self.parse_structured_records(path))
            if ocr_payload["tables"]:
                facts["reconstructed_tables"] = ocr_payload["tables"]
            risk_flags = self.detect_risk_flags(text, rule.document_type)
            metadata = {
                "file_size": path.stat().st_size,
                "page_count": self.page_count(path),
                "signals_expected": list(rule.expected_signals),
                "ocr_required": not bool(text.strip()),
                "ocr_strategy": "native_pdf_text_or_existing_ocr_services",
                "extraction_source": extraction_source,
                "ocr_engine": ocr_payload.get("engine"),
                "page_confidences": ocr_payload["page_confidences"],
                "ocr_confidence": ocr_payload["ocr_confidence"],
                "bounding_boxes": ocr_payload["bounding_boxes"],
            }
            result = {
                "document_name": path.name,
                "document_type": rule.document_type,
                "category": rule.category,
                "source_path": str(path),
                "language": "en",
                "extracted_text": text[:15000],
                "structured_data": facts,
                "risk_flags": risk_flags,
                "metadata_json": metadata,
                "processing_status": "completed" if text.strip() or facts.get("gst_returns") or facts.get("bank_transactions") else "needs_review",
                "confidence_score": self.estimate_confidence(text, facts, native_confidence, ocr_payload["ocr_confidence"]),
            }
        except Exception as exc:
            result = self.failed_document_result(path, str(exc))
        with self._cache_lock:
            self._cache[cache_key] = dict(result)
        return result

    def extract_text(self, path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            try:
                reader = PdfReader(str(path))
                parts = []
                page_limit = 8 if self.demo_mode else 20
                for page in reader.pages[:page_limit]:
                    parts.append(page.extract_text() or "")
                return "\n".join(parts).strip()
            except PdfReadError:
                if self.enable_ocr_fallback:
                    ocr_payload = self.ocr_service.extract_pdf(path, native_text="")
                    return ocr_payload.get("text", "").strip()
                return ""
        if path.suffix.lower() in {".json", ".txt", ".csv"}:
            return path.read_text(encoding="utf-8", errors="ignore")
        return ""

    def page_count(self, path: Path) -> int | None:
        if path.suffix.lower() != ".pdf":
            return None
        try:
            return len(PdfReader(str(path)).pages)
        except Exception:
            return None

    def failed_document_result(self, path: Path, error_message: str) -> dict:
        rule = classify_document(path.name)
        return {
            "document_name": path.name,
            "document_type": rule.document_type,
            "category": rule.category,
            "source_path": str(path),
            "language": "en",
            "extracted_text": "",
            "structured_data": {"document_label": path.name, "error": error_message, "keywords": []},
            "risk_flags": [f"Processing failure: {error_message[:140]}"],
            "metadata_json": {
                "file_size": path.stat().st_size if path.exists() else 0,
                "page_count": None,
                "signals_expected": list(rule.expected_signals),
                "ocr_required": True,
                "ocr_strategy": "native_pdf_text_or_existing_ocr_services",
                "extraction_source": "failed",
                "page_confidences": [],
                "ocr_confidence": 0.0,
                "bounding_boxes": [],
            },
            "processing_status": "failed",
            "confidence_score": 0.0,
        }

    def extract_financial_facts(self, text: str, filename: str) -> dict:
        rupee_matches = re.findall(r"(?:Rs\.?|INR|₹)\s?([\d,]+(?:\.\d+)?)", text, flags=re.IGNORECASE)
        percentages = re.findall(r"(\d+(?:\.\d+)?)\s?%", text)
        entities = self.ner_service.extract(text)
        ner_summary = self.ner_service.summarize(entities)
        return {
            "document_label": filename,
            "currency_amounts_detected": rupee_matches[:25],
            "percentages_detected": percentages[:25],
            "cin": ner_summary["cin"],
            "pan": ner_summary["pan"],
            "gstin": ner_summary["gstin"],
            "keywords": self.top_keywords(text),
            "financial_commitments": self.financial_commitments(text),
            "entities": [entity.to_dict() for entity in entities[:150]],
            "entity_counts": ner_summary["entity_counts"],
            "monetary_amounts_inr": ner_summary["monetary_amounts_inr"],
            "organisations": ner_summary["organisations"],
            "persons": ner_summary["persons"],
            "credit_ratings": ner_summary["ratings"],
            "invalid_identifiers": ner_summary["invalid_identifiers"],
        }

    def parse_structured_records(self, path: Path) -> dict:
        """Detect GST-return and bank-statement tables in CSV / JSON uploads."""
        suffix = path.suffix.lower()
        rows: list[dict] = []
        try:
            if suffix == ".csv":
                raw = path.read_text(encoding="utf-8-sig", errors="ignore")
                reader = csv.DictReader(io.StringIO(raw))
                rows = [{(k or "").strip().lower(): (v or "").strip() for k, v in row.items()} for row in reader]
            elif suffix == ".json":
                payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
                if isinstance(payload, dict):
                    parsed = {}
                    if isinstance(payload.get("gst_returns"), list):
                        parsed["gst_returns"] = payload["gst_returns"]
                    if isinstance(payload.get("bank_transactions"), list):
                        parsed["bank_transactions"] = payload["bank_transactions"]
                    return parsed
                rows = payload if isinstance(payload, list) else []
        except (UnicodeDecodeError, json.JSONDecodeError, csv.Error):
            return {}
        if not rows or not isinstance(rows[0], dict):
            return {}
        columns = {str(key).lower() for key in rows[0]}
        if GST_RETURN_COLUMNS <= columns:
            return {"gst_returns": rows}
        if BANK_COLUMNS <= columns:
            return {"bank_transactions": rows}
        return {}

    def top_keywords(self, text: str) -> list[str]:
        candidates = re.findall(r"[A-Za-z][A-Za-z\-]{4,}", text.lower())
        stop_words = {"there", "their", "which", "these", "those", "other", "under", "company", "limited"}
        freq: dict[str, int] = {}
        for token in candidates:
            if token in stop_words:
                continue
            freq[token] = freq.get(token, 0) + 1
        top = sorted(freq.items(), key=lambda item: item[1], reverse=True)[:12]
        return [token for token, _ in top]

    def detect_risk_flags(self, text: str, document_type: str) -> list[str]:
        lowered = text.lower()
        flags = []
        keyword_map = {
            "litigation": "Litigation-related terminology detected",
            "default": "Default-related reference detected",
            "overdue": "Overdue wording detected",
            "qualified opinion": "Auditor qualification detected",
            "going concern": "Going concern wording detected",
            "fraud": "Fraud wording detected",
            "npa": "NPA wording detected",
            "related party": "Related party disclosure detected",
        }
        for needle, message in keyword_map.items():
            if needle in lowered:
                flags.append(message)
        if document_type == "gst_filing" and "2a" in lowered and "3b" in lowered:
            flags.append("GST reconciliation document includes both GSTR-2A/2B and GSTR-3B references")
        return flags

    def estimate_confidence(self, text: str, facts: dict, native_confidence: float | None = None, ocr_confidence: float | None = None) -> float:
        score = 0.35
        if text:
            score += 0.25
        if any(facts.get(key) for key in ("cin", "pan", "gstin")):
            score += 0.2
        if facts.get("currency_amounts_detected") or facts.get("monetary_amounts_inr"):
            score += 0.1
        if facts.get("gst_returns") or facts.get("bank_transactions"):
            score += 0.15
        if facts.get("keywords"):
            score += 0.1
        if native_confidence is not None:
            score += native_confidence * 0.08
        if ocr_confidence is not None:
            score += ocr_confidence * 0.05
        return round(min(score, 0.98), 2)

    def estimate_native_confidence(self, text: str) -> float:
        if not text:
            return 0.0
        printable = sum(char.isprintable() for char in text)
        alpha_num = sum(char.isalnum() for char in text)
        density = min(len(text) / 1600, 1.0)
        ratio = min(alpha_num / max(printable, 1), 1.0)
        return round(min(0.95, 0.2 + density * 0.4 + ratio * 0.35), 4)

    def financial_commitments(self, text: str) -> list[str]:
        commitments = []
        patterns = [
            r"(term loan[^\.]{0,120})",
            r"(working capital[^\.]{0,120})",
            r"(debenture[^\.]{0,120})",
            r"(guarantee[^\.]{0,120})",
            r"(sanction[^\.]{0,120})",
            r"(contingent liabilit[^\.]{0,120})",
        ]
        lowered = text.lower()
        for pattern in patterns:
            for match in re.findall(pattern, lowered):
                commitments.append(" ".join(match.split())[:140])
        return commitments[:10]

    def summarize_document_mix(self, documents: list[dict]) -> dict:
        by_type: dict[str, int] = {}
        total_flags = 0
        for doc in documents:
            by_type[doc["document_type"]] = by_type.get(doc["document_type"], 0) + 1
            total_flags += len(doc.get("risk_flags") or [])
        return {
            "document_count": len(documents),
            "document_mix": by_type,
            "risk_flag_count": total_flags,
        }

    def export_processing_schema(self) -> dict:
        return {
            "application": [
                "borrower_name",
                "borrower_pan",
                "borrower_gstin",
                "cin",
                "sector",
                "requested_amount",
                "requested_tenor_months",
                "notes",
            ],
            "source_document": [
                "document_type",
                "category",
                "source_path",
                "extracted_text",
                "structured_data",
                "risk_flags",
                "metadata_json.ocr_required",
                "metadata_json.extraction_source",
                "metadata_json.bounding_boxes",
                "confidence_score",
            ],
            "feature_vector": [
                "gst_consistency_score",
                "cash_flow_stability_score",
                "profitability_score",
                "leverage_score",
                "litigation_risk_score",
                "governance_score",
                "management_overlay_score",
                "sector_headwind_score",
                "esg_adjustment_score",
            ],
        }
