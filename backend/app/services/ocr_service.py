from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

from PyPDF2 import PdfReader


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


@dataclass
class OCRLine:
    text: str
    confidence: float
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def y_center(self) -> float:
        return (self.y0 + self.y1) / 2

    @property
    def height(self) -> float:
        return max(self.y1 - self.y0, 1.0)


@dataclass
class OCRPageResult:
    page_number: int
    text: str
    confidence: float
    bounding_boxes: list[dict[str, Any]]
    lines: list[OCRLine]


class _RapidOCREngine:
    """Lazy, process-wide RapidOCR (ONNX Runtime) engine; inference is serialised with a lock."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        from rapidocr_onnxruntime import RapidOCR

        self._engine = RapidOCR()
        self._run_lock = threading.Lock()

    @classmethod
    def get(cls) -> "_RapidOCREngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def read(self, image) -> list[tuple[list, str, float]]:
        import numpy as np

        with self._run_lock:
            result, _ = self._engine(np.asarray(image.convert("RGB")))
        return result or []


class OCRService:
    """OCR for scanned PDFs and images.

    Pages are rasterised with pypdfium2 and read with RapidOCR (PP-OCR models on ONNX Runtime).
    Each line keeps its confidence and bounding box (in PDF points, top-left origin), and tables
    are reconstructed by clustering lines into rows by vertical position. When no OCR engine is
    installed the service falls back to the PDF's embedded text and reports engine "none".
    """

    def __init__(self, demo_mode: bool = True, engine: str = "auto", render_scale: float = 2.0):
        self.demo_mode = demo_mode
        self.render_scale = render_scale
        self.requested_engine = engine
        self._engine = None
        self._engine_name = None

    @property
    def page_limit(self) -> int:
        return 8 if self.demo_mode else 25

    @property
    def engine_name(self) -> str:
        if self._engine_name is None:
            self._resolve_engine(load=False)
        return self._engine_name

    def _resolve_engine(self, load: bool = True):
        if self.requested_engine == "none":
            self._engine_name = "none"
            return None
        try:
            import pypdfium2  # noqa: F401
            import rapidocr_onnxruntime  # noqa: F401
        except ImportError:
            self._engine_name = "none"
            return None
        self._engine_name = "rapidocr"
        if load and self._engine is None:
            self._engine = _RapidOCREngine.get()
        return self._engine

    def extract_pdf(self, path: Path, native_text: str = "") -> dict[str, Any]:
        engine = self._resolve_engine()
        pages = self._ocr_pdf_pages(path, engine) if engine else self._native_pages(path, native_text)
        return self._build_payload(pages)

    def extract_image(self, path: Path) -> dict[str, Any]:
        engine = self._resolve_engine()
        if engine is None:
            return self._build_payload([])
        from PIL import Image

        with Image.open(path) as image:
            page = self._ocr_image(image, page_number=1, scale=1.0, engine=engine)
        return self._build_payload([page])

    # ------------------------------------------------------------------ OCR paths
    def _ocr_pdf_pages(self, path: Path, engine) -> list[OCRPageResult]:
        import pypdfium2 as pdfium

        pages: list[OCRPageResult] = []
        pdf = pdfium.PdfDocument(str(path))
        try:
            for index in range(min(len(pdf), self.page_limit)):
                bitmap = pdf[index].render(scale=self.render_scale)
                pages.append(self._ocr_image(bitmap.to_pil(), index + 1, self.render_scale, engine))
        finally:
            pdf.close()
        return pages

    def _ocr_image(self, image, page_number: int, scale: float, engine) -> OCRPageResult:
        lines: list[OCRLine] = []
        for polygon, text, score in engine.read(image):
            xs = [point[0] for point in polygon]
            ys = [point[1] for point in polygon]
            lines.append(
                OCRLine(
                    text=str(text).strip(),
                    confidence=round(float(score), 4),
                    x0=round(min(xs) / scale, 1),
                    y0=round(min(ys) / scale, 1),
                    x1=round(max(xs) / scale, 1),
                    y1=round(max(ys) / scale, 1),
                )
            )
        rows = self._group_rows(lines)
        text = "\n".join("  ".join(line.text for line in row) for row in rows)
        confidence = round(sum(line.confidence for line in lines) / len(lines), 4) if lines else 0.0
        boxes = [
            {"page": page_number, "text": line.text[:180], "x0": line.x0, "y0": line.y0, "x1": line.x1, "y1": line.y1,
             "confidence": line.confidence}
            for line in lines
        ]
        return OCRPageResult(page_number, text, confidence, boxes, lines)

    def _native_pages(self, path: Path, native_text: str) -> list[OCRPageResult]:
        try:
            reader = PdfReader(str(path))
            texts = [(page.extract_text() or "").strip() for page in reader.pages[: self.page_limit]]
        except Exception:
            texts = [native_text]
        return [
            OCRPageResult(index + 1, text, self._estimate_text_confidence(text), [], [])
            for index, text in enumerate(texts)
        ]

    # ------------------------------------------------------------------ layout helpers
    @staticmethod
    def _group_rows(lines: list[OCRLine]) -> list[list[OCRLine]]:
        if not lines:
            return []
        tolerance = 0.6 * median(line.height for line in lines)
        rows: list[list[OCRLine]] = []
        for line in sorted(lines, key=lambda item: item.y_center):
            if rows and abs(line.y_center - rows[-1][0].y_center) <= tolerance:
                rows[-1].append(line)
            else:
                rows.append([line])
        return [sorted(row, key=lambda item: item.x0) for row in rows]

    def _reconstruct_tables(self, pages: list[OCRPageResult]) -> list[dict[str, Any]]:
        tables = []
        for page in pages:
            rows = self._group_rows(page.lines)
            table_rows = [
                [cell.text for cell in row]
                for row in rows
                if len(row) >= 2 and sum(char.isdigit() for cell in row for char in cell.text) >= 2
            ]
            if len(table_rows) >= 2:
                tables.append(
                    {
                        "table_id": f"page_{page.page_number}_table_1",
                        "page": page.page_number,
                        "detection_method": "ocr_layout_rows",
                        "row_count": len(table_rows),
                        "column_count": max(len(row) for row in table_rows),
                        "rows": table_rows[:25],
                    }
                )
        return tables

    def _build_payload(self, pages: list[OCRPageResult]) -> dict[str, Any]:
        text = "\n".join(page.text for page in pages).strip()
        page_confidences = [page.confidence for page in pages] or [0.0]
        return {
            "engine": self.engine_name,
            "text": text,
            "page_confidences": page_confidences,
            "ocr_confidence": round(sum(page_confidences) / len(page_confidences), 4),
            "tables": self._reconstruct_tables(pages),
            "bounding_boxes": [box for page in pages for box in page.bounding_boxes][:500],
        }

    @staticmethod
    def _estimate_text_confidence(text: str) -> float:
        if not text:
            return 0.0
        alpha = sum(char.isalpha() for char in text)
        numeric = sum(char.isdigit() for char in text)
        printable = sum(char.isprintable() for char in text)
        density = min(len(text) / 1200, 1.0)
        balance = min((alpha + numeric) / max(printable, 1), 1.0)
        return round(min(0.98, 0.35 + density * 0.35 + balance * 0.28), 4)
