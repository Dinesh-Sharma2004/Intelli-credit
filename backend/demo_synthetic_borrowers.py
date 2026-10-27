"""Run the synthetic borrowers through a *running* backend over HTTP.

    python backend/run_flask.py                       # terminal 1
    python backend/demo_synthetic_borrowers.py        # terminal 2  (generate data first:
                                                      #   cd backend && python -m synthetic_data.generator)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

MANIFEST = Path(__file__).resolve().parent / "data" / "synthetic" / "manifest.json"


def run(base_url: str, slug: str, info: dict) -> dict:
    created = requests.post(f"{base_url}/applications", json=info["application"], timeout=30)
    created.raise_for_status()
    application_id = created.json()["id"]
    files = [("documents", (Path(p).name, open(p, "rb"))) for p in info["files"].values()]
    try:
        ingest = requests.post(f"{base_url}/applications/{application_id}/documents/ingest", files=files, timeout=300)
    finally:
        for _, (_, handle) in files:
            handle.close()
    ingest.raise_for_status()
    decision = requests.post(f"{base_url}/applications/{application_id}/decision",
                             json={"officer_input": info["officer_input"]}, timeout=600)
    decision.raise_for_status()
    body = decision.json()
    scorecard = body["scorecard"]
    return {
        "application_id": application_id,
        "borrower": info["application"]["borrower_name"],
        "decision": scorecard["decision"],
        "pd": scorecard["probability_of_default"],
        "grade": scorecard["risk_grade"],
        "limit_inr": scorecard["recommended_limit"],
        "rate": scorecard["recommended_rate"],
        "method": scorecard["explanation_method"],
        "top_drivers": [(d["feature"], d["contribution"]) for d in scorecard["shap_explanation"][:3]],
        "gst_flags": body["anomaly_result"]["anomaly_flags"],
        "research": {h["source_name"]: h["severity"] for h in body["research_hits"]},
        "evidence_method": body["transformer_explainability"].get("method"),
        "cam_pdf": f"{base_url}/applications/{application_id}/cam/pdf",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://127.0.0.1:5000/api/v1")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    for slug, info in manifest["borrowers"].items():
        print(json.dumps({slug: run(args.base_url, slug, info)}, indent=2))


if __name__ == "__main__":
    main()
