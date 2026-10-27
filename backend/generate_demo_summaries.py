from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


BASE_DIR = Path(__file__).resolve().parent
BATCH_REPORT = BASE_DIR / "attached_pdf_pipeline_report.json"
JUDGE_SUMMARY = BASE_DIR / "judge_demo_summary.md"
COMPANY_SPLIT = BASE_DIR / "company_wise_pipeline_report.json"


def load_report() -> dict:
    if not BATCH_REPORT.exists():
        raise FileNotFoundError(f"Batch report not found: {BATCH_REPORT}")
    return json.loads(BATCH_REPORT.read_text(encoding="utf-8"))


def generate_company_split(report: dict) -> dict:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for document in report["documents"]:
        grouped[document["inferred_company"]].append(document)

    company_report = {}
    for company, documents in grouped.items():
        avg_confidence = mean(doc["confidence_score"] for doc in documents)
        avg_grounding = mean(doc["grounding_metrics"]["overall_grounding"] for doc in documents)
        company_report[company] = {
            "document_count": len(documents),
            "document_types": sorted({doc["document_type"] for doc in documents}),
            "average_confidence": round(avg_confidence, 4),
            "average_grounding": round(avg_grounding, 4),
            "risk_flags": sorted({flag for doc in documents for flag in doc["risk_flags"]}),
            "documents": [
                {
                    "document_name": doc["document_name"],
                    "document_type": doc["document_type"],
                    "confidence_score": doc["confidence_score"],
                    "grounding": doc["grounding_metrics"]["overall_grounding"],
                    "preview": doc["text_preview"],
                }
                for doc in documents
            ],
        }
    return company_report


def generate_judge_summary(report: dict, company_split: dict) -> str:
    scorecard = report["scorecard"]
    extraction = report["transformer_extraction_accuracy_proxy"]
    explainability = report["xgboost_style_explainability_accuracy"]
    document_mix = report["processed_documents_summary"]["document_mix"]

    lines = []
    lines.append("# Intelli-Credit Credit Assessment Summary")
    lines.append("")
    lines.append("## 1. Executive Overview")
    lines.append(
        "This report summarises the Intelli-Credit backend pipeline across the attached document set, "
        "including document extraction, secondary research, regulatory mapping, and explainable scoring."
    )
    lines.append("")
    lines.append(f"- Total documents processed: `{report['processed_documents_summary']['document_count']}`")
    lines.append(
        f"- Document composition: `annual reports {document_mix.get('annual_report', 0)}`, "
        f"`sustainability reports {document_mix.get('sustainability_report', 0)}`, "
        f"`generic PDFs {document_mix.get('generic_pdf', 0)}`"
    )
    lines.append(f"- Document-level risk flags identified: `{report['processed_documents_summary']['risk_flag_count']}`")
    lines.append("")
    lines.append("## 2. Credit Recommendation")
    lines.append(f"- Recommended decision: `{scorecard['decision'].upper()}`")
    lines.append(f"- Risk grade: `{scorecard['risk_grade']}`")
    lines.append(f"- Probability of default: `{scorecard['probability_of_default'] * 100:.2f}%`")
    lines.append(f"- Recommended sanction limit: `₹{scorecard['recommended_limit'] / 10000000:.2f} Cr`")
    lines.append(f"- Recommended pricing: `{scorecard['recommended_rate'] * 100:.2f}%`")
    lines.append(f"- Decision summary: {scorecard['explanation_summary']}")
    lines.append("")
    lines.append("## 3. Explainability Summary")
    lines.append(
        f"- Directional faithfulness of score explanations: `{explainability['directional_faithfulness']}`"
    )
    lines.append(
        f"- Top-3 explanation overlap on recomputation: `{explainability['top3_overlap_with_recomputed_explanations']}`"
    )
    lines.append("")
    lines.append("### Principal score drivers")
    for item in report["scorecard"]["shap_explanation"][:5]:
        impact = "Adverse" if item["impact"] == "negative_to_credit" else "Supportive"
        lines.append(f"- `{item['feature']}`: `{item['contribution']:+.4f}` ({impact})")
    lines.append("")
    lines.append("## 4. Extraction Quality")
    lines.append(f"- Average overall grounding: `{extraction['average_overall_grounding']}`")
    lines.append(f"- Identifier grounding: `{extraction['average_identifier_grounding']}`")
    lines.append(f"- Keyword grounding: `{extraction['average_keyword_grounding']}`")
    lines.append(f"- Risk-flag grounding: `{extraction['average_risk_flag_grounding']}`")
    lines.append("")
    lines.append("## 5. Company-Wise View")
    for company, details in company_split.items():
        lines.append(f"### {company}")
        lines.append(f"- Documents reviewed: `{details['document_count']}`")
        lines.append(f"- Document types: `{', '.join(details['document_types'])}`")
        lines.append(f"- Average extraction confidence: `{details['average_confidence']}`")
        lines.append(f"- Average grounding score: `{details['average_grounding']}`")
        lines.append(f"- Key risk flags: `{', '.join(details['risk_flags']) if details['risk_flags'] else 'None reported'}`")
        for document in details["documents"]:
            lines.append(
                f"- `{document['document_name']}` [{document['document_type']}] confidence `{document['confidence_score']}`, grounding `{document['grounding']}`"
            )
        lines.append("")
    lines.append("## 6. Regulatory Coverage")
    for check in report["compliance_checks"]:
        lines.append(
            f"- `{check['regulation_code']}`: `{check['status']}` - {check['regulation_name']}"
        )
    lines.append("")
    lines.append("## 7. Important Caveat")
    lines.append(
        "- The attached PDF set spans multiple inferred borrower entities. Accordingly, the aggregated score shown here is suitable for demonstration of pipeline capability, but not for final underwriting of a single borrower without borrower-specific document segregation."
    )
    return "\n".join(lines)


def main():
    report = load_report()
    company_split = generate_company_split(report)
    COMPANY_SPLIT.write_text(json.dumps(company_split, indent=2), encoding="utf-8")
    JUDGE_SUMMARY.write_text(generate_judge_summary(report, company_split), encoding="utf-8")
    print(f"Wrote {COMPANY_SPLIT}")
    print(f"Wrote {JUDGE_SUMMARY}")


if __name__ == "__main__":
    main()
