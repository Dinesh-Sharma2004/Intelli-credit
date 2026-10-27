from __future__ import annotations

import re
from functools import lru_cache
from statistics import mean
from typing import Any

import numpy as np


FEATURE_QUERY_MAP = {
    "Litigation risk": "evidence of litigation risk, insolvency proceedings, recovery action, default, or legal disputes",
    "Sector headwinds": "evidence of sector headwinds, regulatory tightening, RBI restrictions, liquidity risk, or market stress",
    "Governance": "evidence of strong governance, board oversight, assurance, audit quality, ESG controls, or compliance culture",
    "Risk-flag density": "evidence of risk disclosures, defaults, NPAs, fraud, overdue exposures, or related party concerns",
    "Cash-flow stability": "evidence of stable cash flow, liquidity strength, collections, repayment discipline, or balance sheet resilience",
    "Management overlay": "evidence of management quality, operations execution, capacity utilization, strategic initiatives, or leadership strength",
    "GST consistency": "evidence of GST compliance, GSTR reconciliation, tax transparency, or consistent turnover reporting",
    "Profitability quality": "evidence of profitability, margins, return metrics, earnings quality, or financial performance",
    "GST reconciliation risk": "evidence of GST return mismatch, input tax credit excess, GSTR-1 GSTR-3B difference, or circular trading",
    "Anomaly score": "evidence of unusual transactions, round tripping, related party fund movement, or same-day credits and debits",
    "Early warning score": "evidence of declining EBITDA, rising debtor days, delayed filings, or rating downgrade",
    "Promoter risk": "evidence of promoter disputes, investigations, resignations, or reputational concerns",
    "Leverage headroom": "evidence of debt levels, borrowings, gearing, repayment obligations, or leverage ratios",
}


class TransformerExplainabilityService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", top_k: int = 2, enabled: bool = True):
        self.model_name = model_name
        self.top_k = top_k
        self.enabled = enabled

    def generate(self, documents: list[dict], scorecard: dict, research_hits: list[dict]) -> dict:
        driver_queries = self._driver_queries(scorecard)
        research_queries = self._research_queries(research_hits)
        all_queries = driver_queries + research_queries
        if not all_queries:
            return self._empty_result()

        chunk_records = self._chunk_documents(documents)
        if not chunk_records:
            return self._empty_result()

        try:
            if not self.enabled:
                raise RuntimeError("transformer explainability disabled")
            ranked = self._semantic_rank(all_queries, chunk_records)
            method = "sentence-transformer"
        except Exception as exc:
            ranked = self._keyword_rank(all_queries, chunk_records)
            method = f"keyword-fallback:{exc.__class__.__name__}"

        driver_evidence = [item for item in ranked if item["query_type"] == "score_driver"]
        research_evidence = [item for item in ranked if item["query_type"] == "research_agent"]
        scores = [item["top_similarity"] for item in ranked if item["top_similarity"] is not None]

        return {
            "method": method,
            "model_name": self.model_name,
            "average_evidence_score": round(mean(scores), 4) if scores else 0.0,
            "driver_evidence": driver_evidence,
            "research_evidence": research_evidence,
        }

    def _driver_queries(self, scorecard: dict) -> list[dict]:
        queries = []
        for item in scorecard.get("shap_explanation", [])[:5]:
            query = FEATURE_QUERY_MAP.get(item["feature"])
            if not query:
                continue
            queries.append(
                {
                    "label": item["feature"],
                    "query_type": "score_driver",
                    "query_text": query,
                    "impact": item["impact"],
                }
            )
        return queries

    def _research_queries(self, research_hits: list[dict]) -> list[dict]:
        queries = []
        for hit in research_hits[:4]:
            queries.append(
                {
                    "label": hit["title"],
                    "query_type": "research_agent",
                    "query_text": f"{hit['title']}. {hit['summary']}",
                    "impact": hit.get("severity", "medium"),
                    "source_name": hit.get("source_name"),
                }
            )
        return queries

    def _chunk_documents(self, documents: list[dict]) -> list[dict]:
        chunks: list[dict] = []
        for document in documents:
            text = (document.get("extracted_text") or "").strip()
            if not text:
                continue
            normalized = re.sub(r"\s+", " ", text)
            parts = self._split_text(normalized)
            for index, chunk in enumerate(parts):
                chunks.append(
                    {
                        "document_name": document["document_name"],
                        "document_type": document["document_type"],
                        "chunk_index": index,
                        "text": chunk,
                    }
                )
        return chunks

    def _split_text(self, text: str, chunk_size: int = 650, overlap: int = 120) -> list[str]:
        if len(text) <= chunk_size:
            return [text]
        sentences = re.split(r"(?<=[\.\?!])\s+", text)
        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) + 1 <= chunk_size:
                current = f"{current} {sentence}".strip()
            else:
                if current:
                    chunks.append(current)
                current = sentence
        if current:
            chunks.append(current)
        if not chunks:
            chunks = [text[i : i + chunk_size] for i in range(0, len(text), max(chunk_size - overlap, 1))]
        return chunks[:40]

    def _semantic_rank(self, queries: list[dict], chunk_records: list[dict]) -> list[dict]:
        model = self._load_model(self.model_name)
        query_embeddings = model.encode([item["query_text"] for item in queries], convert_to_numpy=True)
        chunk_embeddings = model.encode([item["text"] for item in chunk_records], convert_to_numpy=True)
        query_embeddings = self._normalize(query_embeddings)
        chunk_embeddings = self._normalize(chunk_embeddings)
        similarity = np.matmul(query_embeddings, chunk_embeddings.T)

        results = []
        for query_index, query in enumerate(queries):
            ranked_indices = np.argsort(similarity[query_index])[::-1][: self.top_k]
            evidence = []
            for chunk_index in ranked_indices:
                chunk = chunk_records[int(chunk_index)]
                evidence.append(
                    {
                        "document_name": chunk["document_name"],
                        "document_type": chunk["document_type"],
                        "chunk_index": chunk["chunk_index"],
                        "similarity": round(float(similarity[query_index][chunk_index]), 4),
                        "snippet": chunk["text"][:420],
                    }
                )
            results.append(
                {
                    "label": query["label"],
                    "query_type": query["query_type"],
                    "impact": query["impact"],
                    "query_text": query["query_text"],
                    "source_name": query.get("source_name"),
                    "top_similarity": evidence[0]["similarity"] if evidence else None,
                    "evidence": evidence,
                }
            )
        return results

    def _keyword_rank(self, queries: list[dict], chunk_records: list[dict]) -> list[dict]:
        results = []
        for query in queries:
            tokens = [token for token in re.findall(r"[a-zA-Z]{4,}", query["query_text"].lower()) if token]
            scored = []
            for chunk in chunk_records:
                lowered = chunk["text"].lower()
                overlap = sum(lowered.count(token) for token in tokens)
                score = overlap / max(len(tokens), 1)
                scored.append((score, chunk))
            scored.sort(key=lambda item: item[0], reverse=True)
            evidence = []
            for score, chunk in scored[: self.top_k]:
                evidence.append(
                    {
                        "document_name": chunk["document_name"],
                        "document_type": chunk["document_type"],
                        "chunk_index": chunk["chunk_index"],
                        "similarity": round(float(score), 4),
                        "snippet": chunk["text"][:420],
                    }
                )
            results.append(
                {
                    "label": query["label"],
                    "query_type": query["query_type"],
                    "impact": query["impact"],
                    "query_text": query["query_text"],
                    "source_name": query.get("source_name"),
                    "top_similarity": evidence[0]["similarity"] if evidence else None,
                    "evidence": evidence,
                }
            )
        return results

    def _empty_result(self) -> dict:
        return {
            "method": "none",
            "model_name": self.model_name,
            "average_evidence_score": 0.0,
            "driver_evidence": [],
            "research_evidence": [],
        }

    def _normalize(self, array: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(array, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return array / norms

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_model(model_name: str) -> Any:
        from sentence_transformers import SentenceTransformer

        try:
            return SentenceTransformer(model_name, local_files_only=True)
        except Exception:
            return SentenceTransformer(model_name)
