from __future__ import annotations

import json
import logging
import math
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np


logger = logging.getLogger(__name__)

LEGAL_SUFFIXES = {"private", "pvt", "limited", "ltd", "llp", "the", "and", "co", "company", "india", "corporation"}

# Severity lexicon for public risk signals (weight in [0, 1]); negative weights are mitigants.
RISK_LEXICON: list[tuple[str, float]] = [
    (r"\b(insolvency|cirp|ibc|section 7|section 9)\b", 0.9),
    (r"\bnclt\b", 0.85),
    (r"\bwilful default(er)?\b", 0.95),
    (r"\b(fraud|forensic audit|money laundering|pmla)\b", 0.9),
    (r"\b(enforcement directorate|ed raid|cbi|sfio|income tax search)\b", 0.85),
    (r"\b(winding up|liquidation)\b", 0.9),
    (r"\b(npa|non-performing|default(ed)?)\b", 0.75),
    (r"\b(recovery suit|drt|debt recovery|sarfaesi)\b", 0.7),
    (r"\b(cheque bounce|section 138|dishonour)\b", 0.55),
    (r"\b(downgrade|negative outlook|rating watch)\b", 0.6),
    (r"\b(show cause|penalty|fine|non-compliance)\b", 0.45),
    (r"\b(delay(ed)?|late filing|overdue)\b", 0.35),
    (r"\b(resign(ed|ation)|auditor change)\b", 0.4),
    (r"\b(strike|layoff|shutdown|closure)\b", 0.45),
    (r"\b(tighten(ing|s)?|restriction|risk weight|curbs?)\b", 0.4),
    (r"\b(slowdown|stress|headwind|oversupply|price pressure)\b", 0.4),
    (r"\b(upgrade|stable outlook|dismissed|settled|acquitted|order win|record demand|robust)\b", -0.3),
]


@dataclass
class CorpusDocument:
    doc_id: str
    source: str
    title: str
    text: str
    url: str = ""
    entity: str | None = None
    sector: str | None = None
    published: date | None = None
    tags: list[str] = field(default_factory=list)

    @property
    def content(self) -> str:
        return f"{self.title}. {self.text}"


def normalize_name(name: str | None) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", (name or "").lower())
    return {token for token in tokens if token not in LEGAL_SUFFIXES}


def name_match(a: str | None, b: str | None) -> float:
    """Token Jaccard similarity of company names with legal suffixes removed."""
    left, right = normalize_name(a), normalize_name(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


ABBREVIATIONS = ("rs.", "pvt.", "ltd.", "co.", "mr.", "mrs.", "ms.", "dr.", "smt.", "vs.", "inc.", "sec.")


def split_sentences(text: str) -> list[str]:
    """Sentence split that does not break after Indian-finance abbreviations like 'Rs.' or 'Pvt.'."""
    sentences: list[str] = []
    for piece in re.split(r"(?<=[.!?])\s+", text.strip()):
        if sentences and (sentences[-1].lower().endswith(ABBREVIATIONS) or piece[:1].isdigit()):
            sentences[-1] = f"{sentences[-1]} {piece}"
        elif piece:
            sentences.append(piece)
    return sentences


def risk_severity(text: str) -> float:
    lowered = text.lower()
    hits = [weight for pattern, weight in RISK_LEXICON if re.search(pattern, lowered)]
    positives = [w for w in hits if w < 0]
    negatives = sorted((w for w in hits if w > 0), reverse=True)
    if not negatives:
        return round(max(0.0, 0.05 + sum(positives)), 4)
    score = negatives[0] + 0.05 * (len(negatives) - 1) + 0.5 * sum(positives)
    return round(min(max(score, 0.0), 1.0), 4)


class PublicRiskSignalCorpus:
    """JSONL corpus of public risk signals (registry filings, court records, news, regulator notes)."""

    def __init__(self, path: Path | None):
        self.path = Path(path) if path else None
        self.documents: list[CorpusDocument] = self._load()

    def _load(self) -> list[CorpusDocument]:
        if not self.path or not self.path.exists():
            logger.warning("Research corpus not found at %s", self.path)
            return []
        documents = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            published = row.get("date")
            documents.append(
                CorpusDocument(
                    doc_id=str(row["id"]),
                    source=row["source"],
                    title=row.get("title", ""),
                    text=row.get("text", ""),
                    url=row.get("url", ""),
                    entity=row.get("entity"),
                    sector=row.get("sector"),
                    published=datetime.strptime(published, "%Y-%m-%d").date() if published else None,
                    tags=list(row.get("tags", [])),
                )
            )
        return documents


class HybridRetriever:
    """TF-IDF (word 1-2 grams) retrieval, optionally fused with MiniLM dense similarity."""

    def __init__(self, documents: list[CorpusDocument], enable_dense: bool = False):
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.documents = documents
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english", min_df=1)
        self.matrix = self.vectorizer.fit_transform([doc.content for doc in documents]) if documents else None
        self.dense_matrix = None
        self.encoder = None
        self.method = "tfidf"
        if enable_dense and documents:
            try:
                from sentence_transformers import SentenceTransformer

                self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
                self.dense_matrix = self.encoder.encode([doc.content for doc in documents], normalize_embeddings=True)
                self.method = "hybrid-tfidf-minilm"
            except Exception as exc:  # model unavailable offline
                logger.warning("Dense retrieval disabled: %s", exc)

    def similarities(self, query: str) -> np.ndarray:
        if self.matrix is None:
            return np.zeros(0)
        sparse = (self.matrix @ self.vectorizer.transform([query]).T).toarray().ravel()
        if self.dense_matrix is not None:
            dense = self.dense_matrix @ self.encoder.encode([query], normalize_embeddings=True)[0]
            return 0.5 * sparse + 0.5 * np.clip(dense, 0, None)
        return sparse

    def sentence_scores(self, query: str, sentences: list[str]) -> np.ndarray:
        if not sentences:
            return np.zeros(0)
        query_vec = self.vectorizer.transform([query])
        return (self.vectorizer.transform(sentences) @ query_vec.T).toarray().ravel()


@dataclass(frozen=True)
class Connector:
    key: str
    source_name: str
    finding_type: str
    scope: str              # "entity" (borrower-specific) or "sector"
    query: str
    risk_field: str
    source_url: str


CONNECTORS: tuple[Connector, ...] = (
    Connector("mca", "MCA", "registry", "entity",
              "{borrower} annual return filing charge director resignation auditor compliance", "promoter_risk_score",
              "https://www.mca.gov.in/"),
    Connector("ecourts", "e-Courts", "litigation", "entity",
              "{borrower} litigation suit petition court NCLT insolvency recovery cheque dishonour", "litigation_severity_index",
              "https://ecourts.gov.in/"),
    Connector("news", "News", "media", "entity",
              "{borrower} promoter fraud raid investigation default expansion order news", "promoter_risk_score",
              "https://news.google.com/"),
    Connector("rbi", "RBI", "sector_regulation", "sector",
              "{sector} RBI circular regulation guidelines risk weight liquidity", "sector_headwind_score",
              "https://www.rbi.org.in/"),
    Connector("sector", "Sector Intelligence", "sector_signal", "sector",
              "{sector} sector outlook demand prices margins stress capacity", "sector_headwind_score",
              "https://intelli-credit.local/sector"),
)


class ResearchService:
    """Retrieval-augmented research agent over public risk signals.

    For each connector (MCA, e-Courts, News, RBI, sector) it retrieves the most relevant corpus
    documents, restricted to the borrower (entity connectors) or its sector (sector connectors),
    scores them with a severity lexicon and recency decay, and writes an extractive summary with
    evidence citations. Connectors run in parallel with a timeout and degrade to a neutral
    "no public signal" finding instead of inventing risk scores.
    """

    def __init__(
        self,
        workers: int = 4,
        timeout_seconds: int = 8,
        demo_mode: bool = True,
        corpus_path: Path | None = None,
        enable_dense: bool = False,
        top_k: int = 3,
    ):
        self.workers = workers
        self.timeout_seconds = timeout_seconds
        self.demo_mode = demo_mode
        self.top_k = top_k
        self.corpus = PublicRiskSignalCorpus(corpus_path)
        self.retriever = HybridRetriever(self.corpus.documents, enable_dense=enable_dense)
        dated = [doc.published for doc in self.corpus.documents if doc.published]
        # Recency is measured against the newest signal so results are reproducible.
        self.as_of = max(dated) if dated else date.today()

    @property
    def corpus_size(self) -> int:
        return len(self.corpus.documents)

    @property
    def retrieval_method(self) -> str:
        return self.retriever.method if self.corpus.documents else "none"

    def run_parallel_research(self, borrower_name: str, sector: str | None = None) -> list[dict]:
        sector_name = sector or "Indian corporates"
        findings: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            future_map = {
                executor.submit(self.run_connector, connector, borrower_name, sector_name): connector
                for connector in CONNECTORS
            }
            try:
                for future in as_completed(future_map, timeout=self.timeout_seconds):
                    connector = future_map[future]
                    try:
                        findings[connector.key] = future.result(timeout=0)
                    except Exception as exc:
                        logger.warning("Connector %s failed: %s", connector.key, exc)
                        findings[connector.key] = self._fallback(connector, borrower_name, sector_name, "error")
            except TimeoutError:
                pass
        for connector in CONNECTORS:
            findings.setdefault(connector.key, self._fallback(connector, borrower_name, sector_name, "timeout"))
        return [findings[connector.key] for connector in CONNECTORS]

    # ------------------------------------------------------------------ retrieval + summarisation
    def retrieve(self, connector: Connector, borrower_name: str, sector: str) -> list[dict]:
        query = connector.query.format(borrower=borrower_name, sector=sector)
        similarities = self.retriever.similarities(query)
        ranked = []
        for index, doc in enumerate(self.corpus.documents):
            if doc.source != connector.source_name:
                continue
            if connector.scope == "entity":
                match = name_match(doc.entity, borrower_name)
                if match < 0.6:
                    continue
            else:
                match = name_match(doc.sector, sector)
                if doc.sector not in (None, "all") and match == 0.0:
                    continue
            relevance = float(similarities[index]) if len(similarities) else 0.0
            ranked.append(
                {
                    "document": doc,
                    "relevance": round(relevance + 0.25 * match, 4),
                    "severity": risk_severity(doc.content),
                    "recency_weight": self._recency(doc.published),
                }
            )
        ranked.sort(key=lambda item: (item["relevance"], item["document"].doc_id), reverse=True)
        return ranked[: self.top_k], query

    def run_connector(self, connector: Connector, borrower_name: str, sector: str) -> dict:
        evidence, query = self.retrieve(connector, borrower_name, sector)
        if not evidence:
            return self._no_signal(connector, borrower_name, sector)

        weights = [item["recency_weight"] for item in evidence]
        severities = [item["severity"] for item in evidence]
        material = sum(1 for s in severities if s >= 0.5)
        risk = max(s * w for s, w in zip(severities, weights)) + 0.05 * max(material - 1, 0)
        risk = round(min(max(risk, 0.0), 1.0), 4)
        summary = self._extractive_summary(query, evidence)
        sentiment = "negative" if risk >= 0.5 else "positive" if risk <= 0.1 else "neutral"
        severity = "high" if risk >= 0.7 else "medium" if risk >= 0.4 else "low"
        subject = borrower_name if connector.scope == "entity" else sector
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "retrieval_method": self.retrieval_method,
            connector.risk_field: risk,
            "evidence": [
                {
                    "citation": f"E{rank + 1}",
                    "id": item["document"].doc_id,
                    "title": item["document"].title,
                    "url": item["document"].url,
                    "date": item["document"].published.isoformat() if item["document"].published else None,
                    "relevance": item["relevance"],
                    "severity": item["severity"],
                }
                for rank, item in enumerate(evidence)
            ],
        }
        alerts = [item["document"].title for item in evidence if item["severity"] >= 0.4]
        if alerts and connector.key in {"mca", "rbi", "ecourts"}:
            payload["regulatory_alerts"] = alerts
        if connector.key == "ecourts":
            payload["early_warning_signals"] = [t for item in evidence for t in item["document"].tags][:6]
        return {
            "source_name": connector.source_name,
            "title": f"{connector.source_name} findings for {subject}",
            "source_url": evidence[0]["document"].url or connector.source_url,
            "finding_type": connector.finding_type,
            "summary": summary,
            "sentiment": sentiment,
            "severity": severity,
            "payload": payload,
        }

    def _extractive_summary(self, query: str, evidence: list[dict], max_sentences: int = 3) -> str:
        candidates = []
        for rank, item in enumerate(evidence):
            for sentence in split_sentences(item["document"].text):
                if len(sentence.split()) >= 5:
                    candidates.append((sentence.strip(), rank))
        if not candidates:
            return " ".join(f"{item['document'].title} [E{rank + 1}]" for rank, item in enumerate(evidence))
        relevance = self.retriever.sentence_scores(query, [sentence for sentence, _ in candidates])
        scored = [
            (relevance[i] + 0.6 * risk_severity(sentence) + 0.1 * (len(evidence) - rank), i)
            for i, (sentence, rank) in enumerate(candidates)
        ]
        chosen = sorted(sorted(scored, reverse=True)[:max_sentences], key=lambda item: item[1])
        return " ".join(f"{candidates[i][0]} [E{candidates[i][1] + 1}]" for _, i in chosen)

    def _recency(self, published: date | None) -> float:
        if published is None:
            return 0.8
        age_days = max((self.as_of - published).days, 0)
        return round(math.exp(-age_days / 730), 4)          # ~2-year decay

    def _no_signal(self, connector: Connector, borrower_name: str, sector: str) -> dict:
        subject = borrower_name if connector.scope == "entity" else sector
        return {
            "source_name": connector.source_name,
            "title": f"No {connector.source_name} signals found for {subject}",
            "source_url": connector.source_url,
            "finding_type": "no_public_signal",
            "summary": f"The research agent found no {connector.source_name} records matching {subject} in the indexed corpus.",
            "sentiment": "neutral",
            "severity": "low",
            "payload": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "retrieval_method": self.retrieval_method,
                connector.risk_field: 0.0,
                "evidence": [],
            },
        }

    def _fallback(self, connector: Connector, borrower_name: str, sector: str, reason: str) -> dict:
        finding = self._no_signal(connector, borrower_name, sector)
        finding.update(
            {
                "title": f"{connector.source_name} connector {reason} for {borrower_name}",
                "finding_type": "fallback",
                "summary": f"Connector {reason}; no evidence retrieved. Manual research required.",
            }
        )
        finding["payload"]["regulatory_alerts"] = [f"{connector.source_name} research incomplete ({reason})"]
        return finding

    # ------------------------------------------------------------------ aggregation
    def build_research_graph(self, findings: list[dict]) -> dict:
        promoter_risk = 0.0
        litigation_risk = 0.0
        sector_headwind = 0.0
        regulatory_alerts: list[str] = []

        for finding in findings:
            payload = finding.get("payload") or {}
            promoter_risk = max(promoter_risk, float(payload.get("promoter_risk_score", 0.0)))
            litigation_risk = max(litigation_risk, float(payload.get("litigation_severity_index", 0.0)))
            sector_headwind = max(sector_headwind, float(payload.get("sector_headwind_score", 0.0)))
            regulatory_alerts.extend(payload.get("regulatory_alerts", []))

        sector_outlook = "negative" if sector_headwind >= 0.6 else "watch" if sector_headwind >= 0.4 else "stable"
        return {
            "promoter_risk": round(promoter_risk, 4),
            "litigation_risk": round(litigation_risk, 4),
            "sector_headwind": round(sector_headwind, 4),
            "sector_outlook": sector_outlook,
            "regulatory_alerts": sorted(set(regulatory_alerts)),
        }
