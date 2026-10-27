from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import mean

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import Config
from app.services.document_service import DocumentProcessingService
from run_attached_pdf_pipeline import ATTACHED_PDFS


OUTPUT_PATH = Path(__file__).resolve().parent / "transformer_pdf_explainability_report.json"
PIPELINE_REPORT_PATH = Path(__file__).resolve().parent / "attached_pdf_pipeline_report.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

FEATURE_QUERY_MAP = {
    "Litigation risk": "evidence of litigation risk, insolvency proceedings, recovery action, default, or legal disputes",
    "Sector headwinds": "evidence of sector headwinds, regulatory tightening, RBI restrictions, liquidity risk, or market stress",
    "Governance": "evidence of strong governance, board oversight, assurance, audit quality, ESG controls, or compliance culture",
    "Risk-flag density": "evidence of risk disclosures, defaults, NPAs, fraud, overdue exposures, or related party concerns",
    "Cash-flow stability": "evidence of stable cash flow, liquidity strength, collections, repayment discipline, or balance sheet resilience",
    "Management overlay": "evidence of management quality, operations execution, capacity utilization, strategic initiatives, or leadership strength",
    "GST consistency": "evidence of GST compliance, GSTR reconciliation, tax transparency, or consistent turnover reporting",
    "Profitability quality": "evidence of profitability, margins, return metrics, earnings quality, or financial performance",
}

RISK_FLAG_QUERY_MAP = {
    "Fraud wording detected": "evidence mentioning fraud, misconduct, misstatement, or investigation",
    "Default-related reference detected": "evidence mentioning default, delayed repayment, covenant breach, or credit stress",
    "NPA wording detected": "evidence mentioning non-performing assets, NPA, stressed assets, or impaired loans",
    "Related party disclosure detected": "evidence mentioning related party transactions, promoter-linked exposure, or connected dealings",
    "Going concern wording detected": "evidence mentioning going concern uncertainty, solvency pressure, or material uncertainty",
    "Auditor qualification detected": "evidence mentioning auditor qualification, adverse opinion, emphasis of matter, or reservation",
    "Overdue wording detected": "evidence mentioning overdue receivables, delayed payments, or past due obligations",
    "Litigation-related terminology detected": "evidence mentioning lawsuits, claims, disputes, courts, or insolvency proceedings",
}


def load_driver_queries() -> list[dict]:
    if not PIPELINE_REPORT_PATH.exists():
        raise FileNotFoundError(f"Pipeline report not found: {PIPELINE_REPORT_PATH}")

    report = json.loads(PIPELINE_REPORT_PATH.read_text(encoding="utf-8"))
    queries: list[dict] = []

    for item in report["scorecard"]["shap_explanation"][:5]:
        query_text = FEATURE_QUERY_MAP.get(item["feature"])
        if query_text:
            queries.append(
                {
                    "label": item["feature"],
                    "type": "score_driver",
                    "impact": item["impact"],
                    "query": query_text,
                }
            )

    risk_flags = sorted({flag for doc in report["documents"] for flag in doc.get("risk_flags", [])})
    for risk_flag in risk_flags:
        query_text = RISK_FLAG_QUERY_MAP.get(risk_flag)
        if query_text:
            queries.append(
                {
                    "label": risk_flag,
                    "type": "risk_flag",
                    "impact": "negative_to_credit",
                    "query": query_text,
                }
            )

    return queries


def split_into_chunks(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    sentences = re.split(r"(?<=[\.\?!])\s+", normalized)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if not sentence:
            continue
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current} {sentence}".strip()
            continue

        if current:
            chunks.append(current)
        if len(sentence) <= chunk_size:
            current = sentence
        else:
            start = 0
            while start < len(sentence):
                part = sentence[start : start + chunk_size]
                chunks.append(part.strip())
                start += max(chunk_size - overlap, 1)
            current = ""

    if current:
        chunks.append(current)

    deduped: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        key = chunk[:180]
        if key not in seen:
            seen.add(key)
            deduped.append(chunk)
    return deduped[:80]


def cosine_similarity_matrix(query_embeddings: np.ndarray, chunk_embeddings: np.ndarray) -> np.ndarray:
    query_norm = query_embeddings / np.linalg.norm(query_embeddings, axis=1, keepdims=True)
    chunk_norm = chunk_embeddings / np.linalg.norm(chunk_embeddings, axis=1, keepdims=True)
    return np.matmul(query_norm, chunk_norm.T)


def process_documents() -> list[dict]:
    doc_service = DocumentProcessingService(Config.UPLOAD_DIR, workers=Config.PARALLEL_WORKERS)
    imported_paths = doc_service.import_existing_paths(ATTACHED_PDFS)
    return doc_service.process_documents_parallel(imported_paths)


def main() -> None:
    model = SentenceTransformer(MODEL_NAME)
    queries = load_driver_queries()
    documents = process_documents()

    query_texts = [item["query"] for item in queries]
    query_embeddings = model.encode(query_texts, convert_to_numpy=True, normalize_embeddings=False)

    explained_documents: list[dict] = []
    document_scores: list[float] = []

    for document in documents:
        text = document.get("extracted_text") or ""
        chunks = split_into_chunks(text)
        if not chunks:
            explained_documents.append(
                {
                    "document_name": document["document_name"],
                    "document_type": document["document_type"],
                    "evidence_coverage_score": 0.0,
                    "top_evidence": [],
                }
            )
            document_scores.append(0.0)
            continue

        chunk_embeddings = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=False)
        similarity = cosine_similarity_matrix(query_embeddings, chunk_embeddings)

        top_evidence = []
        top_scores = []
        for query_index, query_info in enumerate(queries):
            ranked_indices = np.argsort(similarity[query_index])[::-1][:3]
            evidence = []
            for chunk_index in ranked_indices:
                score = float(similarity[query_index][chunk_index])
                evidence.append(
                    {
                        "similarity": round(score, 4),
                        "chunk_text": chunks[chunk_index][:500],
                    }
                )
            top_score = evidence[0]["similarity"] if evidence else 0.0
            top_scores.append(top_score)
            top_evidence.append(
                {
                    "label": query_info["label"],
                    "type": query_info["type"],
                    "impact": query_info["impact"],
                    "query": query_info["query"],
                    "top_similarity": top_score,
                    "evidence_chunks": evidence,
                }
            )

        coverage_score = round(mean(top_scores), 4) if top_scores else 0.0
        document_scores.append(coverage_score)
        explained_documents.append(
            {
                "document_name": document["document_name"],
                "document_type": document["document_type"],
                "risk_flags": document.get("risk_flags") or [],
                "confidence_score": document.get("confidence_score", 0.0),
                "evidence_coverage_score": coverage_score,
                "top_evidence": top_evidence,
            }
        )

    report = {
        "model_name": MODEL_NAME,
        "documents_evaluated": len(explained_documents),
        "driver_queries": queries,
        "average_evidence_coverage_score": round(mean(document_scores), 4) if document_scores else 0.0,
        "documents": explained_documents,
    }

    OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Transformer PDF explainability completed")
    print("=" * 40)
    print(f"Documents evaluated: {report['documents_evaluated']}")
    print(f"Average evidence coverage score: {report['average_evidence_coverage_score']}")
    print(f"Report saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
