"""End-to-end: the three synthetic personas through upload -> OCR/NER -> reconciliation -> research -> PD -> CAM."""
from pathlib import Path

import pytest

from conftest import run_borrower

pytestmark = pytest.mark.ocr


@pytest.fixture(autouse=True)
def _needs_ocr(requires_ocr):
    pass


def decision(results, slug):
    return results[slug]["decision"]


def test_risk_ordering_and_decisions(borrower_results):
    pds = {slug: decision(borrower_results, slug)["scorecard"]["probability_of_default"]
           for slug in ("sunrise-agro", "meridian-steel", "vertex-tradelinks")}
    assert pds["sunrise-agro"] < pds["meridian-steel"] < pds["vertex-tradelinks"]
    assert decision(borrower_results, "sunrise-agro")["scorecard"]["decision"] == "approve"
    assert decision(borrower_results, "meridian-steel")["scorecard"]["decision"] == "review"
    assert decision(borrower_results, "vertex-tradelinks")["scorecard"]["decision"] == "reject"


def test_every_document_is_processed_and_scan_is_ocred(borrower_results, synthetic_data):
    for slug, result in borrower_results.items():
        if slug.startswith("_"):
            continue
        documents = {doc["document_type"]: doc for doc in result["ingest"]["documents"]}
        assert set(documents) == {"annual_report", "rating_report", "gst_filing", "bank_statement"}
        assert all(doc["processing_status"] == "completed" for doc in documents.values())
        assert documents["rating_report"]["metadata_json"]["extraction_source"] == "ocr"
        assert documents["annual_report"]["metadata_json"]["extraction_source"] == "native"


def test_ocr_and_ner_recover_identifiers_matching_the_application(borrower_results, synthetic_data):
    for slug, info in synthetic_data["borrowers"].items():
        docs = decision(borrower_results, slug)["documents"]
        gstins = {doc["structured_data"].get("gstin") for doc in docs if doc["structured_data"].get("gstin")}
        assert gstins == {info["application"]["borrower_gstin"]}
        assert decision(borrower_results, slug)["anomaly_result"]["identity_checks"]["flags"] == []


def test_healthy_borrower_reconciles_cleanly(borrower_results):
    result = decision(borrower_results, "sunrise-agro")
    recon = result["anomaly_result"]["gst_reconciliation"]
    assert recon["flags"] == [] and recon["anomalous_periods"] == []
    assert {c["regulation_code"]: c["status"] for c in result["compliance_checks"]}["GST-RECON"] == "reconciled"
    assert result["early_warning_result"]["early_warning_flags"] == []


def test_fraud_profile_is_caught_by_reconciliation(borrower_results):
    result = decision(borrower_results, "vertex-tradelinks")
    summary = result["anomaly_result"]["gst_reconciliation"]["summary"]
    assert summary["round_trip_pairs"] >= 30
    assert summary["months_itc_excess_breach"] == 12
    assert summary["mean_outward_gap_pct"] > 0.15
    top_drivers = [d["feature"] for d in result["scorecard"]["shap_explanation"][:5]]
    assert {"Litigation risk", "Anomaly score"} <= set(top_drivers)
    assert "Monthly GST-bank reconciliation submission" in result["scorecard"]["covenant_recommendations"]


def test_research_agent_cites_borrower_evidence_and_ignores_lookalikes(borrower_results):
    vertex = {hit["source_name"]: hit for hit in decision(borrower_results, "vertex-tradelinks")["research_hits"]}
    titles = [e["title"] for e in vertex["e-Courts"]["payload"]["evidence"]]
    assert any("NCLT" in title for title in titles)
    assert not any("Vertex Logistics" in title for title in titles)
    assert vertex["e-Courts"]["severity"] == "high" and "[E1]" in vertex["e-Courts"]["summary"]

    sunrise = {hit["source_name"]: hit for hit in decision(borrower_results, "sunrise-agro")["research_hits"]}
    assert sunrise["e-Courts"]["finding_type"] == "no_public_signal"
    assert not any("Sunrise Pharma" in e["title"] for e in sunrise["News"]["payload"]["evidence"])


def test_cam_documents_are_generated(borrower_results):
    for slug in ("sunrise-agro", "meridian-steel", "vertex-tradelinks"):
        cam = decision(borrower_results, slug)["cam_artifact"]
        assert Path(cam["pdf_path"]).exists() and Path(cam["docx_path"]).exists()
        assert cam["memo_json"]["executive_summary"]["decision"] == decision(borrower_results, slug)["scorecard"]["decision"]


def test_tampered_application_pan_is_flagged(client, synthetic_data):
    info = synthetic_data["borrowers"]["sunrise-agro"]
    result = run_borrower(client, info, application_overrides={"borrower_pan": "ZZZCZ9999Z"})
    flags = result["decision"]["anomaly_result"]["identity_checks"]["flags"]
    assert any("PAN on application not found" in flag for flag in flags)
    statuses = {c["regulation_code"]: c["status"] for c in result["decision"]["compliance_checks"]}
    assert statuses["RBI-KYC-AML"] == "exception_found"
