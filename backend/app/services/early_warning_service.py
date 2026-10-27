from __future__ import annotations

import re

RISING_RECEIVABLES = re.compile(
    r"(rose|rising|increase[ds]?|higher|deteriorat\w*|elongat\w*)[^.]{0,40}(debtor|receivable) days"
    r"|(debtor|receivable) days[^.]{0,30}(rose|rising|increase[ds]?|higher|up)"
    r"|collections? (were |was )?delayed"
)


class EarlyWarningService:
    """Builds proactive monitoring flags from extracted document and research signals."""

    def analyze(self, documents: list[dict], research_hits: list[dict], anomaly_result: dict) -> dict:
        text = " ".join((doc.get("extracted_text") or "").lower() for doc in documents)
        flags = []
        score = 0.0

        if any(term in text for term in ("ebitda decline", "margin pressure", "profit decline")):
            flags.append("Declining EBITDA trend reference detected")
            score += 0.18
        if RISING_RECEIVABLES.search(text):
            flags.append("Rising debtor days signal detected")
            score += 0.16
        if any(term in text for term in ("delayed filing", "gst delay", "late filing")):
            flags.append("GST filing delay proxy detected")
            score += 0.14
        if any(term in text for term in ("downgrade", "rating watch", "negative outlook")):
            flags.append("Rating downgrade mention detected")
            score += 0.2

        litigation_mentions = sum(1 for hit in research_hits if hit.get("finding_type") == "litigation")
        if litigation_mentions > 0:
            flags.append("Litigation increase / legal exposure signal")
            score += min(0.12 + litigation_mentions * 0.04, 0.24)

        reconciliation = anomaly_result.get("gst_reconciliation") or {}
        late_filings = (reconciliation.get("summary") or {}).get("late_filings", 0)
        if late_filings >= 2 and "GST filing delay proxy detected" not in flags:
            flags.append(f"GSTR-3B filed late in {late_filings} period(s)")
            score += min(0.06 + late_filings * 0.02, 0.18)
        if (reconciliation.get("summary") or {}).get("round_trip_pairs", 0) >= 3:
            flags.append("Round-trip fund movements in bank statement")
            score += 0.12

        if anomaly_result.get("anomaly_score", 0.0) > 0.35:
            flags.append("Transaction anomaly score elevated")
            score += 0.12

        return {
            "early_warning_flags": flags,
            "early_warning_score": round(min(score, 1.0), 4),
        }
