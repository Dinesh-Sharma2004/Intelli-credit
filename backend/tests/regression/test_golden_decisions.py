"""Golden-output regression: decisions for the synthetic personas must not drift silently.

Regenerate after an intentional change with:  pytest tests/regression --update-golden
"""
import json
from pathlib import Path

import pytest

GOLDEN_DIR = Path(__file__).parent / "golden"
PERSONAS = ("sunrise-agro", "meridian-steel", "vertex-tradelinks")
PD_TOLERANCE = 0.01
SCORE_TOLERANCE = 0.02

pytestmark = pytest.mark.ocr


def snapshot(result: dict) -> dict:
    decision = result["decision"]
    scorecard = decision["scorecard"]
    anomaly = decision["anomaly_result"]
    recon = anomaly["gst_reconciliation"] or {}
    return {
        "decision": scorecard["decision"],
        "risk_grade": scorecard["risk_grade"],
        "probability_of_default": round(scorecard["probability_of_default"], 4),
        "model_version": scorecard["model_version"],
        "top_drivers": [d["feature"] for d in scorecard["shap_explanation"][:3]],
        "anomaly_score": round(anomaly["anomaly_score"], 4),
        "anomaly_flags": sorted(anomaly["anomaly_flags"]),
        "gst_reconciliation_risk": recon.get("risk_score"),
        "reconciliation_counts": {k: (recon.get("summary") or {}).get(k) for k in
                                  ("months_outward_gap_breach", "months_itc_excess_breach", "late_filings", "round_trip_pairs")},
        "research": {hit["source_name"]: [hit["finding_type"], hit["severity"]] for hit in decision["research_hits"]},
        "compliance": {check["regulation_code"]: check["status"] for check in decision["compliance_checks"]},
        "early_warning_flags": sorted(decision["early_warning_result"]["early_warning_flags"]),
        "covenants": scorecard["covenant_recommendations"],
        "extraction_sources": {doc["document_type"]: doc["metadata_json"]["extraction_source"] for doc in result["ingest"]["documents"]},
        "entity_counts": {doc["document_type"]: doc["structured_data"].get("entity_counts", {}) for doc in decision["documents"]},
    }


@pytest.fixture(autouse=True)
def _needs_ocr(requires_ocr):
    pass


@pytest.mark.parametrize("slug", PERSONAS)
def test_decision_matches_golden(slug, borrower_results, update_golden):
    current = snapshot(borrower_results[slug])
    golden_path = GOLDEN_DIR / f"{slug}.json"
    if update_golden or not golden_path.exists():
        GOLDEN_DIR.mkdir(exist_ok=True)
        golden_path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not update_golden:
            pytest.fail(f"golden file {golden_path.name} was missing and has been created; re-run to compare")
        return

    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    assert current["probability_of_default"] == pytest.approx(golden["probability_of_default"], abs=PD_TOLERANCE)
    assert current["anomaly_score"] == pytest.approx(golden["anomaly_score"], abs=SCORE_TOLERANCE)
    if golden["gst_reconciliation_risk"] is not None:
        assert current["gst_reconciliation_risk"] == pytest.approx(golden["gst_reconciliation_risk"], abs=SCORE_TOLERANCE)
    exact = {k: v for k, v in golden.items() if k not in {"probability_of_default", "anomaly_score", "gst_reconciliation_risk"}}
    for key, expected in exact.items():
        assert current[key] == expected, f"{slug}: '{key}' drifted from golden"
