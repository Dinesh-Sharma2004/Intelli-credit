from __future__ import annotations

import re


class QualitativeIntelligenceService:
    """Converts officer notes into structured credit adjustments."""

    NEGATIVE_TERMS = ("delay", "issue", "shutdown", "stress", "weak", "poor", "fraud", "default", "labour", "governance issue")
    POSITIVE_TERMS = ("stable", "strong", "improving", "compliant", "disciplined", "healthy", "efficient")

    def analyze(self, officer_input: dict | None) -> dict:
        officer_input = officer_input or {}
        notes = str(officer_input.get("notes") or "").strip()
        lowered = notes.lower()

        utilization_match = re.search(r"(\d{1,3})\s*%?", lowered)
        utilization_pct = float(utilization_match.group(1)) if utilization_match else float(officer_input.get("capacity_utilization_pct", 75))
        governance_mentions = sum(lowered.count(term) for term in ("governance", "compliance", "audit", "board"))
        labour_mentions = sum(lowered.count(term) for term in ("labour", "worker", "employee unrest"))
        negative_hits = sum(lowered.count(term) for term in self.NEGATIVE_TERMS)
        positive_hits = sum(lowered.count(term) for term in self.POSITIVE_TERMS)

        sentiment_score = max(-1.0, min(1.0, (positive_hits - negative_hits) / max(positive_hits + negative_hits, 1)))
        utilization_penalty = 0.12 if utilization_pct < 50 else 0.06 if utilization_pct < 65 else 0.0
        governance_penalty = min(governance_mentions * 0.03, 0.12) if "issue" in lowered else 0.0
        labour_penalty = min(labour_mentions * 0.04, 0.12)
        note_penalty = max(0.0, -sentiment_score) * 0.12 + utilization_penalty + governance_penalty + labour_penalty

        return {
            "sentiment_score": round(sentiment_score, 4),
            "keywords_detected": sorted(
                {
                    keyword
                    for keyword in ("utilization", "governance", "labour", "capacity", "audit", "compliance", "delay", "stress")
                    if keyword in lowered
                }
            ),
            "utilization_pct_detected": utilization_pct,
            "numeric_adjustments": {
                "management_overlay_delta": round(-note_penalty, 4),
                "governance_delta": round(-(governance_penalty + labour_penalty / 2), 4),
                "capacity_delta": round(-utilization_penalty, 4),
            },
            "summary": self._summary(utilization_pct, sentiment_score, governance_mentions, labour_mentions),
        }

    def _summary(self, utilization_pct: float, sentiment_score: float, governance_mentions: int, labour_mentions: int) -> str:
        fragments = [f"utilization signal {utilization_pct:.0f}%"]
        fragments.append("positive tone" if sentiment_score >= 0 else "negative tone")
        if governance_mentions:
            fragments.append("governance discussed")
        if labour_mentions:
            fragments.append("labour sensitivity flagged")
        return ", ".join(fragments)
