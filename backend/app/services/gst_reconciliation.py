from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from statistics import median
from typing import Any

import numpy as np


GST_RATE_ASSUMPTION = 0.18          # bank receipts include GST on taxable value
OUTWARD_GAP_TOLERANCE = 0.10        # GSTR-1 vs GSTR-3B taxable value
ITC_EXCESS_TOLERANCE = 0.05         # ITC claimed in 3B beyond 2B availability
LOW_BANK_COVERAGE = 0.60            # bank credits far below declared turnover -> inflated sales
HIGH_BANK_COVERAGE = 1.60           # bank credits far above turnover -> unreported sales
ROUND_TRIP_WINDOW_DAYS = 3
ROUND_TRIP_AMOUNT_TOLERANCE = 0.02
ROBUST_Z_THRESHOLD = 3.5
# A statistically unusual period is only reported when it is also material in absolute terms.
MATERIAL_DEVIATION = {"outward_gap_pct": 0.05, "itc_excess_pct": 0.05, "bank_coverage_ratio": 0.25}


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return 0.0


def _to_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


def robust_z_scores(values: list[float]) -> list[float]:
    """Median/MAD z-scores (0.6745 scaling); robust to the very outliers we want to find."""
    if len(values) < 3:
        return [0.0] * len(values)
    center = median(values)
    mad = median(abs(value - center) for value in values)
    if mad == 0:
        return [0.0 if value == center else float("inf") for value in values]
    return [0.6745 * (value - center) / mad for value in values]


class GSTReconciliationService:
    """Reconciles GST returns against each other and against bank statements.

    Checks performed per return period:
      * GSTR-1 vs GSTR-3B outward taxable value (under-reporting of liability)
      * ITC claimed in GSTR-3B vs ITC available in GSTR-2B (excess credit claims)
      * GST turnover vs bank credits (inflated or suppressed sales)
      * late GSTR-3B filing
    plus round-trip detection in the bank statement (same counterparty, matching amount,
    money in and out within a few days) and unsupervised anomaly detection on the monthly
    series (robust z-scores and an Isolation Forest).
    """

    def reconcile(self, gst_rows: list[dict], bank_transactions: list[dict]) -> dict:
        months = self._monthly_table(gst_rows, bank_transactions)
        round_trips = self.detect_round_trips(bank_transactions)
        total_credits = sum(_to_float(txn.get("credit")) for txn in bank_transactions)
        round_trip_volume = sum(pair["amount"] for pair in round_trips)
        round_trip_ratio = round(round_trip_volume / total_credits, 4) if total_credits else 0.0

        gaps = [m["outward_gap_pct"] for m in months if m["outward_gap_pct"] is not None]
        itc = [m["itc_excess_pct"] for m in months if m["itc_excess_pct"] is not None]
        coverage = [m["bank_coverage_ratio"] for m in months if m["bank_coverage_ratio"] is not None]
        late = [m for m in months if (m["filing_delay_days"] or 0) > 0]

        summary = {
            "periods_analysed": len(months),
            "mean_outward_gap_pct": round(float(np.mean(gaps)), 4) if gaps else 0.0,
            "months_outward_gap_breach": sum(1 for g in gaps if g > OUTWARD_GAP_TOLERANCE),
            "mean_itc_excess_pct": round(float(np.mean(itc)), 4) if itc else 0.0,
            "months_itc_excess_breach": sum(1 for x in itc if x > ITC_EXCESS_TOLERANCE),
            "median_bank_coverage_ratio": round(float(median(coverage)), 4) if coverage else None,
            "late_filings": len(late),
            "max_filing_delay_days": max((m["filing_delay_days"] or 0 for m in months), default=0),
            "round_trip_pairs": len(round_trips),
            "round_trip_volume": round(round_trip_volume, 2),
            "round_trip_ratio": round_trip_ratio,
        }
        anomalous_periods = self.detect_anomalous_periods(months)
        flags = self._flags(summary, anomalous_periods)
        return {
            "summary": summary,
            "risk_score": self._risk_score(summary),
            "components": self._components(summary),
            "flags": flags,
            "anomalous_periods": anomalous_periods,
            "round_trips": round_trips[:25],
            "monthly": months,
        }

    # ------------------------------------------------------------------ building blocks
    def _monthly_table(self, gst_rows: list[dict], bank_transactions: list[dict]) -> list[dict]:
        credits_by_month: dict[str, float] = defaultdict(float)
        for txn in bank_transactions:
            txn_date = _to_date(txn.get("date"))
            if txn_date:
                credits_by_month[txn_date.strftime("%Y-%m")] += _to_float(txn.get("credit"))

        months = []
        for row in sorted(gst_rows, key=lambda r: str(r.get("period"))):
            period = str(row.get("period"))[:7]
            gstr1 = _to_float(row.get("gstr1_taxable_value"))
            gstr3b = _to_float(row.get("gstr3b_taxable_value"))
            itc_claimed = _to_float(row.get("itc_claimed_3b"))
            itc_available = _to_float(row.get("itc_available_2b"))
            filed, due = _to_date(row.get("filing_date_3b")), _to_date(row.get("due_date_3b"))
            bank_credit = credits_by_month.get(period) if bank_transactions else None
            months.append(
                {
                    "period": period,
                    "gstr1_taxable_value": gstr1,
                    "gstr3b_taxable_value": gstr3b,
                    "outward_gap_pct": round(abs(gstr1 - gstr3b) / gstr1, 4) if gstr1 else None,
                    "itc_claimed_3b": itc_claimed,
                    "itc_available_2b": itc_available,
                    "itc_excess_pct": round(max(itc_claimed - itc_available, 0.0) / itc_available, 4) if itc_available else None,
                    "bank_credits": round(bank_credit, 2) if bank_credit is not None else None,
                    "bank_coverage_ratio": (
                        round(bank_credit / (gstr3b * (1 + GST_RATE_ASSUMPTION)), 4)
                        if bank_credit is not None and gstr3b else None
                    ),
                    "filing_delay_days": (filed - due).days if filed and due else None,
                }
            )
        return months

    def detect_round_trips(self, bank_transactions: list[dict]) -> list[dict]:
        """Pair each credit with a later debit to the same counterparty of (almost) the same amount."""
        by_counterparty: dict[str, list[dict]] = defaultdict(list)
        for txn in bank_transactions:
            counterparty = str(txn.get("counterparty") or "").strip().lower()
            txn_date = _to_date(txn.get("date"))
            if counterparty and txn_date:
                by_counterparty[counterparty].append({**txn, "_date": txn_date})

        pairs = []
        for counterparty, txns in by_counterparty.items():
            credits = sorted((t for t in txns if _to_float(t.get("credit")) > 0), key=lambda t: t["_date"])
            debits = sorted((t for t in txns if _to_float(t.get("debit")) > 0), key=lambda t: t["_date"])
            used: set[int] = set()
            for credit in credits:
                amount = _to_float(credit.get("credit"))
                for index, debit in enumerate(debits):
                    if index in used:
                        continue
                    gap = (debit["_date"] - credit["_date"]).days
                    if 0 <= gap <= ROUND_TRIP_WINDOW_DAYS and abs(_to_float(debit.get("debit")) - amount) <= amount * ROUND_TRIP_AMOUNT_TOLERANCE:
                        used.add(index)
                        pairs.append(
                            {
                                "counterparty": credit.get("counterparty"),
                                "credit_date": credit["_date"].isoformat(),
                                "debit_date": debit["_date"].isoformat(),
                                "amount": round(amount, 2),
                                "days_apart": gap,
                            }
                        )
                        break
        return sorted(pairs, key=lambda p: (p["credit_date"], p["counterparty"] or ""))

    @staticmethod
    def _is_material(metric: str, value: float, center: float) -> bool:
        if metric == "bank_coverage_ratio":
            return abs(value - center) >= MATERIAL_DEVIATION[metric] and not (LOW_BANK_COVERAGE <= value <= HIGH_BANK_COVERAGE and abs(value - 1.0) < 0.3)
        tolerance = OUTWARD_GAP_TOLERANCE if metric == "outward_gap_pct" else ITC_EXCESS_TOLERANCE
        return value > tolerance and value - center >= MATERIAL_DEVIATION[metric]

    def detect_anomalous_periods(self, months: list[dict]) -> list[dict]:
        metrics = ["outward_gap_pct", "itc_excess_pct", "bank_coverage_ratio"]
        findings: dict[str, dict] = {}
        centers = {}
        for metric in metrics:
            values = [(m["period"], m[metric]) for m in months if m[metric] is not None]
            if len(values) < 6:
                continue
            centers[metric] = median(v for _, v in values)
            scores = robust_z_scores([v for _, v in values])
            for (period, value), score in zip(values, scores):
                if abs(score) >= ROBUST_Z_THRESHOLD and self._is_material(metric, value, centers[metric]):
                    entry = findings.setdefault(period, {"period": period, "signals": [], "isolation_forest": False})
                    entry["signals"].append({"metric": metric, "value": value, "robust_z": round(score, 2) if np.isfinite(score) else "inf"})

        matrix_rows = [m for m in months if all(m[metric] is not None for metric in metrics)]
        if len(matrix_rows) >= 8:
            from sklearn.ensemble import IsolationForest

            matrix = np.array([[m[metric] for metric in metrics] for m in matrix_rows])
            if np.ptp(matrix, axis=0).sum() > 0:
                forest = IsolationForest(n_estimators=200, contamination=0.1, random_state=0)
                labels = forest.fit_predict(matrix)
                for row, label in zip(matrix_rows, labels):
                    material = any(
                        metric in centers and self._is_material(metric, row[metric], centers[metric]) for metric in metrics
                    )
                    if label == -1 and material:
                        entry = findings.setdefault(row["period"], {"period": row["period"], "signals": [], "isolation_forest": False})
                        entry["isolation_forest"] = True
        return [findings[key] for key in sorted(findings)]

    @staticmethod
    def _components(summary: dict) -> dict:
        coverage = summary["median_bank_coverage_ratio"]
        low_cover = min(max(0.85 - coverage, 0.0) / 0.45, 1.0) if coverage is not None else 0.0
        high_cover = min(max(coverage - HIGH_BANK_COVERAGE, 0.0) / 1.0, 1.0) * 0.5 if coverage is not None else 0.0
        return {
            "outward_gap": round(min(summary["mean_outward_gap_pct"] / 0.20, 1.0), 4),
            "itc_excess": round(min(summary["mean_itc_excess_pct"] / 0.20, 1.0), 4),
            "bank_coverage": round(max(low_cover, high_cover), 4),
            "round_tripping": round(min(summary["round_trip_ratio"] / 0.25, 1.0), 4),
            "late_filing": round(min(summary["late_filings"] / 6, 1.0), 4),
        }

    def _risk_score(self, summary: dict) -> float:
        c = self._components(summary)
        score = (
            0.25 * c["outward_gap"]
            + 0.25 * c["itc_excess"]
            + 0.20 * c["bank_coverage"]
            + 0.20 * c["round_tripping"]
            + 0.10 * c["late_filing"]
        )
        return round(min(score, 1.0), 4)

    @staticmethod
    def _flags(summary: dict, anomalous_periods: list[dict]) -> list[str]:
        flags = []
        if summary["months_outward_gap_breach"]:
            flags.append(
                f"GSTR-1 vs GSTR-3B outward value gap above {OUTWARD_GAP_TOLERANCE:.0%} in "
                f"{summary['months_outward_gap_breach']} period(s)"
            )
        if summary["months_itc_excess_breach"]:
            flags.append(
                f"ITC claimed in GSTR-3B exceeds GSTR-2B availability in {summary['months_itc_excess_breach']} period(s) "
                f"(mean excess {summary['mean_itc_excess_pct']:.1%})"
            )
        coverage = summary["median_bank_coverage_ratio"]
        if coverage is not None and coverage < LOW_BANK_COVERAGE:
            flags.append(f"Bank credits cover only {coverage:.0%} of GST turnover: possible inflated sales")
        if coverage is not None and coverage > HIGH_BANK_COVERAGE:
            flags.append(f"Bank credits are {coverage:.0%} of GST turnover: possible unreported sales")
        if summary["round_trip_pairs"]:
            flags.append(
                f"{summary['round_trip_pairs']} round-trip fund movements detected "
                f"({summary['round_trip_ratio']:.0%} of bank credits): possible circular trading"
            )
        if summary["late_filings"] >= 2:
            flags.append(f"GSTR-3B filed late in {summary['late_filings']} period(s)")
        if anomalous_periods:
            flags.append("Anomalous return periods: " + ", ".join(p["period"] for p in anomalous_periods))
        return flags
