from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from app.services.ocr_service import OCRLine, OCRService


def render_scan(path: Path, lines: list[str], as_pdf: bool = True) -> Path:
    image = Image.new("RGB", (1654, 1200), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=40)
    for index, text in enumerate(lines):
        draw.text((100, 120 + index * 110), text, fill="black", font=font)
    if as_pdf:
        image.save(path, "PDF", resolution=200.0)
    else:
        image.save(path)
    return path


SCAN_LINES = [
    "Bank Sanction Letter",
    "Borrower: Acme Foods Private Limited",
    "Facility        Limit        Rate",
    "Term Loan       450.00       10.5",
    "Cash Credit     125.00       11.2",
]


def test_group_rows_clusters_by_vertical_position():
    lines = [
        OCRLine("B", 0.9, 300, 100, 340, 130),
        OCRLine("A", 0.9, 10, 102, 60, 128),
        OCRLine("C", 0.9, 10, 200, 60, 230),
    ]
    rows = OCRService._group_rows(lines)
    assert [[line.text for line in row] for row in rows] == [["A", "B"], ["C"]]
    assert OCRService._group_rows([]) == []


def test_engine_none_falls_back_to_embedded_text(tmp_path):
    from reportlab.pdfgen import canvas

    path = tmp_path / "text.pdf"
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 720, "Embedded text layer for Acme Foods")
    pdf.save()
    service = OCRService(engine="none")
    payload = service.extract_pdf(path)
    assert payload["engine"] == "none"
    assert "Acme Foods" in payload["text"]
    assert payload["bounding_boxes"] == []
    assert service.extract_image(path)["text"] == ""


@pytest.mark.ocr
def test_scanned_pdf_is_read_with_boxes_and_tables(tmp_path, requires_ocr):
    path = render_scan(tmp_path / "scan.pdf", SCAN_LINES)
    payload = OCRService().extract_pdf(path)
    assert payload["engine"] == "rapidocr"
    text = payload["text"].lower()
    for expected in ("sanction letter", "acme foods", "term loan", "450.00", "11.2"):
        assert expected in text
    assert payload["ocr_confidence"] > 0.7
    # boxes are in PDF points of an 8.27in x 6in page (595 x 432 pt)
    assert payload["bounding_boxes"]
    for box in payload["bounding_boxes"]:
        assert 0 <= box["x0"] < box["x1"] <= 600 and 0 <= box["y0"] < box["y1"] <= 440
    table = payload["tables"][0]
    assert table["detection_method"] == "ocr_layout_rows"
    assert ["Term Loan", "450.00", "10.5"] in table["rows"]


@pytest.mark.ocr
def test_png_image_is_read(tmp_path, requires_ocr):
    path = render_scan(tmp_path / "scan.png", SCAN_LINES[:2], as_pdf=False)
    payload = OCRService().extract_image(path)
    assert "acme foods" in payload["text"].lower()
    assert len(payload["page_confidences"]) == 1


@pytest.mark.ocr
def test_page_limit_is_respected(tmp_path, requires_ocr):
    pages = [Image.new("RGB", (800, 400), "white") for _ in range(3)]
    for index, page in enumerate(pages):
        ImageDraw.Draw(page).text((50, 150), f"Page number {index + 1}", fill="black", font=ImageFont.load_default(size=40))
    path = tmp_path / "multi.pdf"
    pages[0].save(path, "PDF", resolution=100.0, save_all=True, append_images=pages[1:])
    service = OCRService()
    service.demo_mode = True
    payload = service.extract_pdf(path)
    assert len(payload["page_confidences"]) == 3
    assert "page number 3" in payload["text"].lower()
