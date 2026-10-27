from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import mean

from app.config import Config
from app.services.compliance_service import ComplianceService
from app.services.document_catalog import compliance_matrix_for_documents
from app.services.document_service import DocumentProcessingService
from app.services.research_service import ResearchService
from app.services.scoring_service import ScoringService


ATTACHED_PDFS = [
    r"C:\Users\DINESH SHARMA\Downloads\fy24-annual-report-kinara-capital.pdf",
    r"C:\Users\DINESH SHARMA\Downloads\Annual Report FY 2024-25.pdf",
    r"C:\Users\DINESH SHARMA\Downloads\VCL-ANNUAL REPORT FINAL.pdf",
    r"C:\Users\DINESH SHARMA\Downloads\Consolidated Annual report_FY 2022-23.pdf",
    r"C:\Users\DINESH SHARMA\Downloads\Vivriti Sustainability Report 2024-25 2 Sep.pdf",
    r"C:\Users\DINESH SHARMA\Downloads\1754051517.pdf",
    r"C:\Users\DINESH SHARMA\Downloads\1754045722.pdf",
    r"C:\Users\DINESH SHARMA\Downloads\1756892129.pdf",
]

OUTPUT_PATH = Path(__file__).resolve().parent / "attached_pdf_pipeline_report.json"

FEATURE_LABEL_TO_KEY = {
    "GST consistency": "gst_consistency_score",
    "Cash-flow stability": "cash_flow_stability_score",
    "Profitability quality": "profitability_score",
    "Litigation risk": "litigation_risk_score",
    "Sector headwinds": "sector_headwind_score",
    "Management overlay": "management_overlay_score",
    "Governance": "governance_score",
    "Risk-flag density": "risk_flag_density",
}

RISK_FLAG_GROUNDING = {
    "Litigation-related terminology detected": "litigation",
    "Default-related reference detected": "default",
    "Overdue wording detected": "overdue",
    "Auditor qualification detected": "qualified opinion",
    "Going concern wording detected": "going concern",
    "Fraud wording detected": "fraud",
    "NPA wording detected": "npa",
    "Related party disclosure detected": "related party",
    "GST reconciliation document includes both GSTR-2A/2B and GSTR-3B references": "3b",
}


def infer_company_name(text: str, fallback: str) -> str:
    patterns = [
        r"([A-Z][A-Za-z&,\-\. ]{3,80}(?:Limited|Ltd|Private Limited|Pvt Ltd|Pvt\. Ltd\.|Capital))",
        r"([A-Z][A-Za-z&,\-\. ]{3,80}(?:Corporation|Finance|Ventures|Industries))",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return " ".join(match.group(1).split())
    return fallback


def grounding_score(document: dict) -> dict:
    text = (document.get("extracted_text") or "").lower()
    structured = document.get("structured_data") or {}
    identifiers = []
    for key in ("cin", "pan", "gstin"):
        value = structured.get(key)
        if value:
            identifiers.append(1.0 if str(value).lower() in text else 0.0)

    keywords = structured.get("keywords") or []
    keyword_hits = [1.0 if keyword.lower() in text else 0.0 for keyword in keywords if keyword]

    risk_flag_hits = []
    for flag in document.get("risk_flags") or []:
        needle = RISK_FLAG_GROUNDING.get(flag)
        if needle:
            risk_flag_hits.append(1.0 if needle in text else 0.0)

    identifier_grounding = mean(identifiers) if identifiers else 1.0
    keyword_grounding = mean(keyword_hits) if keyword_hits else 1.0
    risk_flag_grounding = mean(risk_flag_hits) if risk_flag_hits else 1.0
    overall = mean([identifier_grounding, keyword_grounding, risk_flag_grounding])

    return {
        "identifier_grounding": round(identifier_grounding, 4),
        "keyword_grounding": round(keyword_grounding, 4),
        "risk_flag_grounding": round(risk_flag_grounding, 4),
        "overall_grounding": round(overall, 4),
    }


def explainability_metrics(scorecard: dict, scoring_service: ScoringService) -> dict:
    feature_vector = scorecard["feature_vector"]
    base_pd = scoring_service.probability_of_default(dict(feature_vector))
    direction_matches = []

    for explanation in scorecard["shap_explanation"]:
        feature_key = FEATURE_LABEL_TO_KEY.get(explanation["feature"])
        if feature_key not in feature_vector:
            continue
        mutated = dict(feature_vector)
        mutated[feature_key] = min(1.0, max(0.0, mutated[feature_key] + 0.1))
        delta = scoring_service.probability_of_default(mutated) - base_pd
        expected_positive = explanation["impact"] == "negative_to_credit"
        direction_matches.append((delta > 0) == expected_positive if delta != 0 else True)

    recalculated = scoring_service.shap_like_explanation(dict(feature_vector))
    stored_top = [item["feature"] for item in scorecard["shap_explanation"][:3]]
    recalculated_top = [item["feature"] for item in recalculated[:3]]
    top3_overlap = len(set(stored_top) & set(recalculated_top)) / max(len(set(stored_top)), 1)

    return {
        "base_pd": round(base_pd, 4),
        "directional_faithfulness": round(mean(direction_matches), 4) if direction_matches else None,
        "top3_overlap_with_recomputed_explanations": round(top3_overlap, 4),
    }


def main():
    upload_dir = Config.UPLOAD_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)

    doc_service = DocumentProcessingService(upload_dir, workers=Config.PARALLEL_WORKERS)
    scoring_service = ScoringService()
    research_service = ResearchService(workers=Config.PARALLEL_WORKERS)
    compliance_service = ComplianceService()

    imported_paths = doc_service.import_existing_paths(ATTACHED_PDFS)
    processed_documents = doc_service.process_documents_parallel(imported_paths)

    enriched_documents = []
    inferred_companies = []
    for document in processed_documents:
        preview = (document.get("extracted_text") or "").replace("\n", " ").strip()[:350]
        inferred_company = infer_company_name(document.get("extracted_text") or "", Path(document["document_name"]).stem)
        inferred_companies.append(inferred_company)
        enriched_documents.append(
            {
                "document_name": document["document_name"],
                "document_type": document["document_type"],
                "category": document["category"],
                "confidence_score": document["confidence_score"],
                "risk_flags": document["risk_flags"],
                "metadata": document["metadata_json"],
                "structured_data": document["structured_data"],
                "text_preview": preview,
                "inferred_company": inferred_company,
                "grounding_metrics": grounding_score(document),
            }
        )

    unique_companies = sorted(set(inferred_companies))
    application = {
        "borrower_name": "Attached PDF Batch Demo",
        "borrower_pan": "",
        "borrower_gstin": "",
        "cin": "",
        "sector": "Corporate lending demo",
        "requested_amount": 250000000.0,
        "requested_tenor_months": 24,
        "notes": "Mixed-company attached PDF demonstration batch",
    }
    officer_input = {
        "capacity_utilization_pct": 65,
        "governance_score": 0.68,
        "management_quality": 7,
        "inventory_observation": 7,
        "customer_concentration": 35,
        "notes": "Batch demonstration run on attached PDFs.",
    }
    research_hits = research_service.run_parallel_research(application["borrower_name"], application["sector"])
    compliance_checks = compliance_service.build_checks(
        [doc["document_name"] for doc in processed_documents], research_hits
    )
    scorecard = scoring_service.score(application, processed_documents, research_hits, officer_input)

    report = {
        "input_files": ATTACHED_PDFS,
        "processed_documents_summary": doc_service.summarize_document_mix(processed_documents),
        "mixed_company_note": "The attached PDFs span multiple inferred companies; the scorecard below is a batch demo score, not a valid single-borrower underwriting decision."
        if len(unique_companies) > 1
        else "Single inferred borrower set.",
        "inferred_companies": unique_companies,
        "documents": enriched_documents,
        "compliance_matrix": compliance_matrix_for_documents([doc["document_name"] for doc in processed_documents]),
        "research_hits": research_hits,
        "compliance_checks": compliance_checks,
        "scorecard": scorecard,
        "xgboost_style_explainability_accuracy": explainability_metrics(scorecard, scoring_service),
        "transformer_extraction_accuracy_proxy": {
            "documents_evaluated": len(enriched_documents),
            "average_identifier_grounding": round(mean(doc["grounding_metrics"]["identifier_grounding"] for doc in enriched_documents), 4),
            "average_keyword_grounding": round(mean(doc["grounding_metrics"]["keyword_grounding"] for doc in enriched_documents), 4),
            "average_risk_flag_grounding": round(mean(doc["grounding_metrics"]["risk_flag_grounding"] for doc in enriched_documents), 4),
            "average_overall_grounding": round(mean(doc["grounding_metrics"]["overall_grounding"] for doc in enriched_documents), 4),
        },
    }

    OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Attached PDF pipeline completed")
    print("=" * 40)
    print(f"Files processed: {len(processed_documents)}")
    print(f"Inferred companies: {', '.join(unique_companies)}")
    print(f"Average extraction grounding: {report['transformer_extraction_accuracy_proxy']['average_overall_grounding']}")
    print(
        f"Directional faithfulness: {report['xgboost_style_explainability_accuracy']['directional_faithfulness']}"
    )
    print(f"Top-3 explanation overlap: {report['xgboost_style_explainability_accuracy']['top3_overlap_with_recomputed_explanations']}")
    print(f"Report saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
