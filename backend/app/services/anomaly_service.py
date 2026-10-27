from __future__ import annotations

from statistics import mean

from .gst_reconciliation import GSTReconciliationService
from .ner_service import is_valid_gstin, pan_from_gstin


class AnomalyService:
    """Anomaly analytics across borrower documents.

    When structured GST returns / bank statements were ingested, the GST reconciliation engine
    drives the score; otherwise narrative keyword heuristics provide a weaker signal. Identifier
    consistency (application PAN vs documents, PAN embedded in GSTIN, GSTIN check digit) is
    checked whenever the application record is supplied.
    """

    def __init__(self, reconciliation_service: GSTReconciliationService | None = None):
        self.reconciliation_service = reconciliation_service or GSTReconciliationService()

    def analyze(self, documents: list[dict], application: dict | None = None) -> dict:
        texts = " ".join((doc.get("extracted_text") or "").lower() for doc in documents)
        structured_docs = [doc.get("structured_data") or {} for doc in documents]
        amounts = self._numbers(structured_docs, "currency_amounts_detected")
        percentages = self._numbers(structured_docs, "percentages_detected")

        anomaly_flags = []
        explanations = []
        score = 0.0

        gst_present = "gst" in texts or any(item.get("gstin") for item in structured_docs)
        bank_present = "bank" in texts or any(doc.get("document_type") == "bank_statement" for doc in documents)

        revenue_growth_mismatch = self._metric_from_keywords(texts, ["growth", "revenue", "sales"], amounts, 0.18)
        circular_loop_signal = self._metric_from_keywords(texts, ["same day", "routing", "round tripping", "related party"], percentages, 0.16)
        receivable_days_anomaly = self._metric_from_keywords(texts, ["receivable", "collection", "debtor"], percentages, 0.12)
        gst_vs_bank_mismatch = 0.22 if gst_present and bank_present and abs(len(amounts) - len(percentages)) > 8 else 0.08
        same_day_loops = 0.18 if "same-day" in texts or "same day" in texts else 0.06

        metrics = {
            "revenue_growth_mismatch": revenue_growth_mismatch,
            "circular_fund_movement": circular_loop_signal,
            "same_day_loops": same_day_loops,
            "receivable_days_anomaly": receivable_days_anomaly,
            "gst_liability_vs_bank_credit_mismatch": gst_vs_bank_mismatch,
        }

        if revenue_growth_mismatch > 0.18:
            anomaly_flags.append("Revenue inflation / growth mismatch signal")
            explanations.append("Documented revenue cues do not align cleanly with available tax or cash-flow style signals.")
            score += 0.2
        if circular_loop_signal > 0.16:
            anomaly_flags.append("Circular movement heuristic triggered")
            explanations.append("Text and numeric patterns indicate possible circular routing or related-party churn.")
            score += 0.2
        if same_day_loops > 0.12:
            anomaly_flags.append("Same-day debit / credit loop heuristic triggered")
            explanations.append("Potential same-day fund movement pattern detected from extracted narrative indicators.")
            score += 0.12
        if receivable_days_anomaly > 0.12:
            anomaly_flags.append("Receivable days anomaly")
            explanations.append("Collections and receivable references suggest elevated working-capital strain.")
            score += 0.16
        if gst_vs_bank_mismatch > 0.18:
            anomaly_flags.append("GST liability vs bank credit mismatch")
            explanations.append("GST style signals and liquidity/cash-flow cues appear inconsistent and warrant review.")
            score += 0.2
        heuristic_score = min(score, 1.0)

        reconciliation = self._reconcile(structured_docs)
        if reconciliation is not None:
            # Structured evidence replaces the narrative heuristics as the primary signal.
            anomaly_flags = list(reconciliation["flags"])
            explanations = [
                "Anomaly score derived from GST return reconciliation and bank-statement analysis.",
            ] + [f"{name.replace('_', ' ')} component {value:.2f}" for name, value in reconciliation["components"].items() if value > 0]
            score = max(reconciliation["risk_score"], heuristic_score * 0.25)
            source = "gst_reconciliation"
        else:
            score = heuristic_score
            source = "narrative_heuristics"

        identity = self._identity_checks(structured_docs, application)
        if identity["flags"]:
            anomaly_flags.extend(identity["flags"])
            score = min(1.0, score + 0.1 * len(identity["flags"]))

        return {
            "anomaly_flags": anomaly_flags,
            "anomaly_score": round(min(score, 1.0), 4),
            "explanations": explanations,
            "anomaly_metrics": {key: round(value, 4) for key, value in metrics.items()},
            "anomaly_source": source,
            "gst_reconciliation": self._compact(reconciliation) if reconciliation else None,
            "identity_checks": identity,
        }

    def _reconcile(self, structured_docs: list[dict]) -> dict | None:
        gst_rows = [row for item in structured_docs for row in (item.get("gst_returns") or [])]
        bank_txns = [txn for item in structured_docs for txn in (item.get("bank_transactions") or [])]
        if not gst_rows:
            return None
        return self.reconciliation_service.reconcile(gst_rows, bank_txns)

    @staticmethod
    def _compact(reconciliation: dict) -> dict:
        return {key: reconciliation[key] for key in ("summary", "risk_score", "components", "flags", "anomalous_periods", "round_trips", "monthly")}

    @staticmethod
    def _identity_checks(structured_docs: list[dict], application: dict | None) -> dict:
        document_pans = {item["pan"] for item in structured_docs if item.get("pan")}
        document_gstins = {item["gstin"] for item in structured_docs if item.get("gstin")}
        invalid = sorted({ident for item in structured_docs for ident in (item.get("invalid_identifiers") or [])})
        flags = []
        application = application or {}
        app_pan = (application.get("borrower_pan") or "").strip().upper()
        app_gstin = (application.get("borrower_gstin") or "").strip().upper()
        if app_pan and document_pans and app_pan not in document_pans:
            flags.append("Borrower PAN on application not found in submitted documents")
        if app_gstin and not is_valid_gstin(app_gstin):
            flags.append("Application GSTIN fails the GSTN check-digit validation")
        if app_gstin and app_pan and is_valid_gstin(app_gstin) and pan_from_gstin(app_gstin) != app_pan:
            flags.append("Application GSTIN does not embed the borrower PAN")
        foreign_gstins = sorted(g for g in document_gstins if app_pan and pan_from_gstin(g) != app_pan)
        if foreign_gstins:
            flags.append(f"Documents reference GSTIN(s) of a different PAN: {', '.join(foreign_gstins[:3])}")
        if invalid:
            flags.append(f"Invalid identifier(s) in documents: {', '.join(invalid[:3])}")
        return {
            "document_pans": sorted(document_pans),
            "document_gstins": sorted(document_gstins),
            "invalid_identifiers": invalid,
            "flags": flags,
        }

    def _numbers(self, structured_docs: list[dict], key: str) -> list[float]:
        numbers: list[float] = []
        for structured in structured_docs:
            for raw in structured.get(key) or []:
                try:
                    numbers.append(float(str(raw).replace(",", "")))
                except Exception:
                    continue
        return numbers

    def _metric_from_keywords(self, text: str, keywords: list[str], values: list[float], baseline: float) -> float:
        hit_count = sum(text.count(keyword) for keyword in keywords)
        volatility = 0.0
        if values:
            avg = mean(values)
            if avg:
                volatility = min(mean(abs(value - avg) for value in values[:25]) / abs(avg), 1.0)
        return min(baseline + hit_count * 0.02 + volatility * 0.2, 0.95)
