"""Latency smoke tests: generous budgets that catch accidental slowdowns (e.g. OCR on every page)."""
import time

import pytest

from app.services.gst_reconciliation import GSTReconciliationService

pytestmark = pytest.mark.slow

INGEST_BUDGET_SECONDS = 30
DECISION_BUDGET_SECONDS = 10


@pytest.mark.ocr
@pytest.mark.parametrize("slug", ["sunrise-agro", "meridian-steel", "vertex-tradelinks"])
def test_pipeline_latency_budget(borrower_results, slug, requires_ocr):
    timings = borrower_results[slug]["timings"]
    assert timings["ingest_seconds"] < INGEST_BUDGET_SECONDS
    assert timings["decision_seconds"] < DECISION_BUDGET_SECONDS


def test_reconciliation_scales_to_large_statements():
    service = GSTReconciliationService()
    gst = [{"period": f"20{20 + i // 12}-{i % 12 + 1:02d}", "gstr1_taxable_value": 1e7, "gstr3b_taxable_value": 1e7,
            "itc_available_2b": 1e5, "itc_claimed_3b": 1e5} for i in range(36)]
    txns = [{"date": f"20{20 + (i // 1000) % 3}-{(i // 80) % 12 + 1:02d}-{i % 28 + 1:02d}", "counterparty": f"Party {i % 150}",
             "credit": 1000 + i if i % 2 else "", "debit": "" if i % 2 else 1000 + i} for i in range(20000)]
    started = time.perf_counter()
    result = service.reconcile(gst, txns)
    assert time.perf_counter() - started < 10
    assert result["summary"]["periods_analysed"] == 36
