from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from app.services.scoring_service import ScoringService


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "storage" / "intelli_credit.db"
OUTPUT_PATH = BASE_DIR / "credit_explainability_report.json"


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


@dataclass
class DocumentGroundingResult:
    document_name: str
    identifier_grounding: float
    keyword_grounding: float
    risk_flag_grounding: float
    overall_grounding: float


def parse_json(value):
    if value in (None, ""):
        return None
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


def fetch_rows(connection: sqlite3.Connection, query: str):
    connection.row_factory = sqlite3.Row
    return connection.execute(query).fetchall()


def evaluate_document_grounding(rows: list[sqlite3.Row]) -> tuple[list[DocumentGroundingResult], dict]:
    results: list[DocumentGroundingResult] = []

    for row in rows:
        text = (row["extracted_text"] or "").lower()
        structured_data = parse_json(row["structured_data"]) or {}
        risk_flags = parse_json(row["risk_flags"]) or []

        identifier_hits = []
        for key in ("cin", "pan", "gstin"):
            value = structured_data.get(key)
            if value:
                identifier_hits.append(1.0 if str(value).lower() in text else 0.0)

        keyword_values = structured_data.get("keywords") or []
        keyword_hits = [1.0 if keyword.lower() in text else 0.0 for keyword in keyword_values if keyword]

        risk_flag_hits = []
        for risk_flag in risk_flags:
            needle = RISK_FLAG_GROUNDING.get(risk_flag)
            if needle:
                risk_flag_hits.append(1.0 if needle in text else 0.0)

        identifier_score = mean(identifier_hits) if identifier_hits else 1.0
        keyword_score = mean(keyword_hits) if keyword_hits else 1.0
        risk_flag_score = mean(risk_flag_hits) if risk_flag_hits else 1.0
        overall_score = mean([identifier_score, keyword_score, risk_flag_score])

        results.append(
            DocumentGroundingResult(
                document_name=row["document_name"],
                identifier_grounding=round(identifier_score, 4),
                keyword_grounding=round(keyword_score, 4),
                risk_flag_grounding=round(risk_flag_score, 4),
                overall_grounding=round(overall_score, 4),
            )
        )

    summary = {
        "documents_evaluated": len(results),
        "average_identifier_grounding": round(mean([r.identifier_grounding for r in results]), 4) if results else None,
        "average_keyword_grounding": round(mean([r.keyword_grounding for r in results]), 4) if results else None,
        "average_risk_flag_grounding": round(mean([r.risk_flag_grounding for r in results]), 4) if results else None,
        "average_overall_grounding": round(mean([r.overall_grounding for r in results]), 4) if results else None,
    }
    return results, summary


def evaluate_scorecard_explainability(rows: list[sqlite3.Row]) -> tuple[list[dict], dict]:
    scoring_service = ScoringService()
    per_application = []

    for row in rows:
        feature_vector = parse_json(row["feature_vector"]) or {}
        stored_shap = parse_json(row["shap_explanation"]) or []
        if not feature_vector or not stored_shap:
            continue

        base_pd = scoring_service.probability_of_default(dict(feature_vector))
        direction_matches = []

        for explanation in stored_shap:
            feature_label = explanation["feature"]
            feature_key = FEATURE_LABEL_TO_KEY.get(feature_label)
            if feature_key not in feature_vector:
                continue

            mutated = dict(feature_vector)
            mutated[feature_key] = min(1.0, max(0.0, mutated[feature_key] + 0.1))
            delta = scoring_service.probability_of_default(mutated) - base_pd
            expected_positive = explanation["impact"] == "negative_to_credit"
            direction_matches.append((delta > 0) == expected_positive if delta != 0 else True)

        recalculated_shap = scoring_service.shap_like_explanation(dict(feature_vector))
        stored_top = [item["feature"] for item in stored_shap[:3]]
        recalculated_top = [item["feature"] for item in recalculated_shap[:3]]
        top3_overlap = len(set(stored_top) & set(recalculated_top)) / max(len(set(stored_top)), 1)

        per_application.append(
            {
                "application_id": row["application_id"],
                "base_pd": round(base_pd, 4),
                "directional_faithfulness": round(mean(direction_matches), 4) if direction_matches else None,
                "top3_overlap_with_recomputed_explanations": round(top3_overlap, 4),
                "stored_decision": row["decision"],
                "stored_risk_grade": row["risk_grade"],
            }
        )

    summary = {
        "applications_evaluated": len(per_application),
        "average_directional_faithfulness": round(
            mean([item["directional_faithfulness"] for item in per_application if item["directional_faithfulness"] is not None]),
            4,
        )
        if per_application
        else None,
        "average_top3_overlap": round(mean([item["top3_overlap_with_recomputed_explanations"] for item in per_application]), 4)
        if per_application
        else None,
    }
    return per_application, summary


def build_report():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    try:
        document_rows = fetch_rows(
            connection,
            """
            SELECT id, document_name, extracted_text, structured_data, risk_flags
            FROM source_documents
            ORDER BY id
            """,
        )
        scorecard_rows = fetch_rows(
            connection,
            """
            SELECT application_id, decision, risk_grade, feature_vector, shap_explanation
            FROM risk_scorecards
            ORDER BY application_id
            """,
        )

        document_results, document_summary = evaluate_document_grounding(document_rows)
        scorecard_results, scorecard_summary = evaluate_scorecard_explainability(scorecard_rows)

        report = {
            "evaluation_target": "Intelli-Credit extracted documents and XGBoost-style explainability proxy",
            "database_path": str(DB_PATH),
            "document_grounding": {
                "summary": document_summary,
                "per_document": [result.__dict__ for result in document_results],
            },
            "scorecard_explainability": {
                "summary": scorecard_summary,
                "per_application": scorecard_results,
            },
            "notes": [
                "Document grounding measures whether extracted identifiers, keywords, and risk flags are traceable to stored source text.",
                "Scorecard explainability uses the current backend scoring service as the XGBoost-style proxy and checks directional faithfulness under feature perturbation.",
                "This evaluates the current prototype implementation, not a separately trained transformer/XGBoost production model.",
            ],
        }

        OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report
    finally:
        connection.close()


def main():
    report = build_report()
    document_summary = report["document_grounding"]["summary"]
    scorecard_summary = report["scorecard_explainability"]["summary"]

    print("Credit Explainability Evaluation")
    print("=" * 40)
    print(f"Documents evaluated: {document_summary['documents_evaluated']}")
    print(f"Average extraction grounding: {document_summary['average_overall_grounding']}")
    print(f"Applications evaluated: {scorecard_summary['applications_evaluated']}")
    print(f"Average directional faithfulness: {scorecard_summary['average_directional_faithfulness']}")
    print(f"Average top-3 explanation overlap: {scorecard_summary['average_top3_overlap']}")
    print(f"Report saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
