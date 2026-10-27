from __future__ import annotations

import math
import re
from statistics import mean

from ..ml.features import FEATURE_LABELS


class ScoringService:
    """Credit scoring: document/research feature pipeline -> PD model -> limit, rate, grade.

    With a trained ``PDModel`` the probability of default comes from XGBoost and drivers are
    exact TreeSHAP attributions; without one, a transparent weighted scorecard is used.
    """

    model_version = "pdf-grounded-hybrid-credit-model-v2"

    def __init__(self, pd_model=None):
        self.pd_model = pd_model

    def score(
        self,
        application: dict,
        documents: list[dict],
        research_hits: list[dict],
        officer_input: dict | None = None,
        qualitative_intelligence: dict | None = None,
        anomaly_result: dict | None = None,
        research_graph: dict | None = None,
        early_warning_result: dict | None = None,
    ) -> dict:
        features = self.build_feature_vector(
            application,
            documents,
            research_hits,
            officer_input or {},
            qualitative_intelligence or {},
            anomaly_result or {},
            research_graph or {},
            early_warning_result or {},
        )
        if self.pd_model is not None:
            attribution = self.pd_model.explain(features)
            pd = min(max(attribution["probability_of_default"], 0.001), 0.999)
            explanations = self.treeshap_explanation(attribution, features)
            model_version = self.pd_model.version
            explanation_method = "xgboost-treeshap"
            shap_base_value = round(attribution["base_value"], 4)
        else:
            pd = self.probability_of_default(features)
            explanations = self.shap_like_explanation(features)
            model_version = self.model_version
            explanation_method = "heuristic-weights"
            shap_base_value = None
        decision = self.decision(pd)
        base_exposure = self.derive_base_exposure(application, documents)
        recommended_limit = self.recommended_limit(base_exposure, features, pd)
        risk_premium = self.risk_premium(pd, features)
        recommended_rate = round(0.09 + risk_premium, 4)
        grade = self.grade(pd)
        return {
            "model_version": model_version,
            "explanation_method": explanation_method,
            "shap_base_value": shap_base_value,
            "probability_of_default": round(pd, 4),
            "risk_grade": grade,
            "recommended_limit": round(recommended_limit, 2),
            "recommended_rate": recommended_rate,
            "decision": decision,
            "score_breakdown": self.score_breakdown(features),
            "shap_explanation": explanations,
            "feature_vector": features,
            "explanation_summary": self.explanation_summary(pd, decision, explanations, features, explanation_method),
            "pd_band": self.pd_band(pd),
            "risk_premium": round(risk_premium, 4),
            "sanction_simulation": self.sanction_simulation(base_exposure, features, pd),
            "scenario_analysis": self.scenario_analysis(base_exposure, features, pd),
            "covenant_recommendations": self.covenant_recommendations(features, anomaly_result or {}, early_warning_result or {}),
        }

    def build_feature_vector(
        self,
        application: dict,
        documents: list[dict],
        research_hits: list[dict],
        officer_input: dict,
        qualitative_intelligence: dict,
        anomaly_result: dict,
        research_graph: dict,
        early_warning_result: dict,
    ) -> dict:
        texts = [self._document_text(doc) for doc in documents]
        combined_text = " ".join(texts).lower()
        structured = [doc.get("structured_data") or {} for doc in documents]
        risk_flags = [flag for doc in documents for flag in (doc.get("risk_flags") or [])]
        confidences = [float(doc.get("confidence_score", 0.0)) for doc in documents]
        annual_reports = [doc for doc in documents if doc["document_type"] == "annual_report"]
        sustainability_docs = [doc for doc in documents if doc["document_type"] == "sustainability_report"]
        litigation_hits = [hit for hit in research_hits if hit["finding_type"] == "litigation"]
        negative_research = [hit for hit in research_hits if hit["sentiment"] == "negative"]

        currency_values = self._all_currency_values(structured)
        percentages = self._all_percentages(structured)
        keyword_counts = self._keyword_signal_counts(combined_text)
        identifier_hits = self._identifier_hit_ratio(structured)
        amount_diversity = min(len(currency_values) / 18, 1.0)
        confidence_mean = mean(confidences) if confidences else 0.5
        requested_amount = float(application.get("requested_amount", 0.0) or 0.0)
        derived_exposure = self.derive_base_exposure(application, documents)

        gst_signal = self._gst_signal_score(combined_text, structured)
        cash_signal = self._cash_flow_signal_score(combined_text, keyword_counts, percentages, amount_diversity)
        profitability_signal = self._profitability_signal_score(combined_text, keyword_counts, percentages, risk_flags)
        leverage_signal = self._leverage_signal_score(combined_text, keyword_counts, risk_flags, derived_exposure, requested_amount)
        litigation_signal = self._litigation_signal_score(
            risk_flags, litigation_hits, combined_text, float(research_graph.get("litigation_risk", 0.0))
        )
        governance_signal = self._governance_signal_score(combined_text, keyword_counts, risk_flags, officer_input)
        management_signal = self._management_overlay_score(officer_input, combined_text)
        sector_signal = self._sector_headwind_score(
            negative_research, combined_text, risk_flags, float(research_graph.get("sector_headwind", 0.0))
        )
        esg_signal = self._esg_signal_score(sustainability_docs, combined_text)
        governance_signal = max(0.05, min(0.98, governance_signal + qualitative_intelligence.get("numeric_adjustments", {}).get("governance_delta", 0.0)))
        management_signal = max(0.02, min(1.0, management_signal + qualitative_intelligence.get("numeric_adjustments", {}).get("management_overlay_delta", 0.0)))
        capacity_adjusted_cash = max(0.05, min(0.98, cash_signal + qualitative_intelligence.get("numeric_adjustments", {}).get("capacity_delta", 0.0)))
        promoter_risk = float(research_graph.get("promoter_risk", 0.0))
        anomaly_score = float(anomaly_result.get("anomaly_score", 0.0))
        early_warning_score = float(early_warning_result.get("early_warning_score", 0.0))
        reconciliation = anomaly_result.get("gst_reconciliation") or {}
        gst_reconciliation_risk = float(reconciliation.get("risk_score", 0.0)) if reconciliation else 0.0
        if reconciliation:
            # Structured GST evidence outweighs keyword cues for GST consistency.
            gst_signal = max(0.05, min(0.98, 0.4 * gst_signal + 0.6 * (1 - gst_reconciliation_risk)))

        return {
            "document_coverage_score": round(min((len(documents) / 6) * 0.7 + confidence_mean * 0.3, 1.0), 4),
            "identifier_coverage_score": round(identifier_hits, 4),
            "amount_signal_score": round(amount_diversity, 4),
            "gst_consistency_score": round(gst_signal, 4),
            "cash_flow_stability_score": round(capacity_adjusted_cash, 4),
            "profitability_score": round(profitability_signal, 4),
            "leverage_score": round(leverage_signal, 4),
            "litigation_risk_score": round(litigation_signal, 4),
            "governance_score": round(governance_signal, 4),
            "management_overlay_score": round(management_signal, 4),
            "sector_headwind_score": round(sector_signal, 4),
            "esg_adjustment_score": round(esg_signal, 4),
            "risk_flag_density": round(min(len(risk_flags) / max(len(documents), 1) / 4, 1.0), 4),
            "anomaly_score": round(anomaly_score, 4),
            "promoter_risk_score": round(promoter_risk, 4),
            "early_warning_score": round(early_warning_score, 4),
            "gst_reconciliation_risk": round(gst_reconciliation_risk, 4),
            "reported_revenue_proxy_cr": round(self._revenue_proxy(currency_values, annual_reports), 4),
            "liquidity_proxy_cr": round(self._liquidity_proxy(currency_values, combined_text), 4),
            "derived_exposure_cr": round(derived_exposure / 1e7, 4),
        }

    def probability_of_default(self, features: dict) -> float:
        positive = (
            features["document_coverage_score"] * 0.05
            + features["identifier_coverage_score"] * 0.05
            + features["gst_consistency_score"] * 0.11
            + features["cash_flow_stability_score"] * 0.12
            + features["profitability_score"] * 0.1
            + features["governance_score"] * 0.08
            + features["management_overlay_score"] * 0.08
        )
        negative = (
            features["litigation_risk_score"] * 0.18
            + features["sector_headwind_score"] * 0.09
            + features["risk_flag_density"] * 0.12
            + features.get("anomaly_score", 0.0) * 0.08
            + features.get("promoter_risk_score", 0.0) * 0.06
            + features.get("early_warning_score", 0.0) * 0.08
            + (1 - features["leverage_score"]) * 0.1
        )
        base = 0.115
        return max(0.02, min(0.42, base + negative - positive + features["esg_adjustment_score"] * 0.01))

    def derive_base_exposure(self, application: dict, documents: list[dict]) -> float:
        requested_amount = float(application.get("requested_amount", 0.0) or 0.0)
        if requested_amount > 0:
            return requested_amount

        structured = [doc.get("structured_data") or {} for doc in documents]
        values = [value for value in self._all_currency_values(structured) if value > 5]
        if not values:
            return 5_00_00_000.0

        top = sorted(values, reverse=True)[:12]
        median_like = top[len(top) // 2]
        if median_like >= 1000:
            return min(median_like * 1_00_000, 25_00_00_000.0)
        if median_like >= 100:
            return min(median_like * 10_00_000, 20_00_00_000.0)
        return min(median_like * 1_00_00_000, 12_00_00_000.0)

    def recommended_limit(self, base_exposure: float, features: dict, pd: float) -> float:
        support = (
            features["gst_consistency_score"] * 0.2
            + features["cash_flow_stability_score"] * 0.22
            + features["profitability_score"] * 0.18
            + features["management_overlay_score"] * 0.12
            + features["governance_score"] * 0.13
            + features["document_coverage_score"] * 0.15
        )
        haircut = max(0.22, 1 - pd * 2.4)
        return base_exposure * support * haircut

    @staticmethod
    def decision(pd: float) -> str:
        """Auto-approve investment grade only (BBB or better); BB/B go to credit committee."""
        if pd < 0.12:
            return "approve"
        if pd < 0.22:
            return "review"
        return "reject"

    def grade(self, pd: float) -> str:
        if pd < 0.03:
            return "AAA"
        if pd < 0.05:
            return "AA"
        if pd < 0.07:
            return "A"
        if pd < 0.09:
            return "BBB+"
        if pd < 0.12:
            return "BBB"
        if pd < 0.16:
            return "BB"
        if pd < 0.22:
            return "B"
        if pd < 0.3:
            return "CCC"
        return "D"

    def shap_like_explanation(self, features: dict) -> list[dict]:
        contributions = {
            "GST consistency": (features["gst_consistency_score"] - 0.5) * -0.2,
            "Cash-flow stability": (features["cash_flow_stability_score"] - 0.5) * -0.22,
            "Profitability quality": (features["profitability_score"] - 0.5) * -0.18,
            "Litigation risk": features["litigation_risk_score"] * 0.24,
            "Sector headwinds": features["sector_headwind_score"] * 0.11,
            "Management overlay": (features["management_overlay_score"] - 0.5) * -0.14,
            "Governance": (features["governance_score"] - 0.5) * -0.14,
            "Risk-flag density": features["risk_flag_density"] * 0.19,
            "Anomaly score": features.get("anomaly_score", 0.0) * 0.16,
            "Promoter risk": features.get("promoter_risk_score", 0.0) * 0.14,
            "Early warning score": features.get("early_warning_score", 0.0) * 0.14,
        }
        explanation = []
        for feature, contribution in sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True):
            explanation.append(
                {
                    "feature": feature,
                    "contribution": round(contribution, 4),
                    "impact": "negative_to_credit" if contribution > 0 else "positive_to_credit",
                    "directional_impact": "negative" if contribution > 0 else "positive",
                    "magnitude": round(abs(contribution), 4),
                    "narrative_reason": self.narrative_reason(feature, contribution, features),
                }
            )
        return explanation

    def treeshap_explanation(self, attribution: dict, features: dict) -> list[dict]:
        explanation = []
        for key, value in attribution["shap_values"].items():
            label = FEATURE_LABELS.get(key, key)
            impact = "neutral" if abs(value) < 1e-4 else "negative_to_credit" if value > 0 else "positive_to_credit"
            explanation.append(
                {
                    "feature": label,
                    "feature_key": key,
                    "feature_value": round(attribution["feature_values"][key], 4),
                    "contribution": round(value, 4),
                    "shap_value": round(value, 4),
                    "impact": impact,
                    "directional_impact": "negative" if value > 0 else "positive" if value < 0 else "neutral",
                    "magnitude": round(abs(value), 4),
                    "narrative_reason": self.narrative_reason(label, value, features),
                }
            )
        return sorted(explanation, key=lambda item: item["magnitude"], reverse=True)

    def score_breakdown(self, features: dict) -> dict:
        return {
            "character": round((features["governance_score"] + (1 - features["litigation_risk_score"])) / 2, 3),
            "capacity": round((features["cash_flow_stability_score"] + features["management_overlay_score"]) / 2, 3),
            "capital": round((features["profitability_score"] + features["leverage_score"]) / 2, 3),
            "collateral": round(max(0.45, features["document_coverage_score"] * 0.82), 3),
            "conditions": round(1 - features["sector_headwind_score"], 3),
        }

    def explanation_summary(
        self, pd: float, decision: str, explanations: list[dict], features: dict, method: str = "heuristic-weights"
    ) -> str:
        top = explanations[:3]
        fragments = [f"{item['feature']} ({item['impact']})" for item in top]
        model_note = (
            "PD estimated by the XGBoost model; drivers are TreeSHAP attributions. "
            if method == "xgboost-treeshap"
            else "PD estimated by the fallback weighted scorecard. "
        )
        return (
            f"Decision {decision.upper()} with PD {pd:.2%}. {model_note}"
            f"The recommendation is grounded in extracted PDF evidence including revenue/liquidity cues, "
            f"risk-flag density, anomaly analytics, regulatory/litigation references, and governance indicators. "
            f"Primary drivers: {', '.join(fragments)}."
        )

    def pd_band(self, pd: float) -> str:
        if pd < 0.05:
            return "low"
        if pd < 0.12:
            return "moderate"
        if pd < 0.2:
            return "elevated"
        return "high"

    def risk_premium(self, pd: float, features: dict) -> float:
        return max(0.01, min(0.09, 0.02 + pd * 0.22 + features.get("anomaly_score", 0.0) * 0.03))

    def sanction_simulation(self, base_exposure: float, features: dict, pd: float) -> dict:
        return {
            "conservative": round(self.recommended_limit(base_exposure * 0.9, features, min(pd + 0.03, 0.42)), 2),
            "base": round(self.recommended_limit(base_exposure, features, pd), 2),
            "aggressive": round(self.recommended_limit(base_exposure * 1.1, features, max(pd - 0.02, 0.02)), 2),
        }

    def scenario_analysis(self, base_exposure: float, features: dict, pd: float) -> dict:
        return {
            "base": {"pd": round(pd, 4), "limit": round(self.recommended_limit(base_exposure, features, pd), 2)},
            "stress": {"pd": round(min(pd + 0.06, 0.42), 4), "limit": round(self.recommended_limit(base_exposure, features, min(pd + 0.06, 0.42)), 2)},
        }

    def covenant_recommendations(self, features: dict, anomaly_result: dict, early_warning_result: dict) -> list[str]:
        covenants = ["Quarterly financial reporting covenant", "No material adverse litigation covenant"]
        if features.get("anomaly_score", 0.0) > 0.2 or anomaly_result.get("anomaly_flags"):
            covenants.append("Monthly GST-bank reconciliation submission")
        if features.get("early_warning_score", 0.0) > 0.15 or early_warning_result.get("early_warning_flags"):
            covenants.append("Enhanced monitoring trigger on EBITDA or collections deterioration")
        if features.get("litigation_risk_score", 0.0) > 0.5:
            covenants.append("Immediate notification of legal notices, NCLT, or recovery filings")
        return covenants

    def narrative_reason(self, feature: str, contribution: float, features: dict) -> str:
        if feature == "Anomaly score":
            return "Structured GST-vs-bank heuristics increased anomaly sensitivity."
        if feature == "Promoter risk":
            return "Secondary research connectors surfaced promoter/media risk indicators."
        if feature == "Early warning score":
            return "Monitoring signals indicate potential deterioration in borrower trajectory."
        if feature == "Litigation risk":
            return "Research and document references increased legal and recovery risk perception."
        if feature == "Governance":
            return "Governance disclosures and officer inputs supported management quality."
        if feature == "GST reconciliation risk":
            return "GSTR-1/3B/2B reconciliation and bank-credit coverage moved the PD."
        if feature == "Leverage headroom":
            return "Debt references and exposure size shaped the leverage assessment."
        return f"{feature} adjusted the calibrated PD through the explainable feature pipeline."

    def _document_text(self, document: dict) -> str:
        return (document.get("extracted_text") or "").lower()

    def _all_currency_values(self, structured_documents: list[dict]) -> list[float]:
        values: list[float] = []
        for structured in structured_documents:
            for raw in structured.get("currency_amounts_detected") or []:
                parsed = self._parse_float(raw)
                if parsed is not None:
                    values.append(parsed)
        return values

    def _all_percentages(self, structured_documents: list[dict]) -> list[float]:
        values: list[float] = []
        for structured in structured_documents:
            for raw in structured.get("percentages_detected") or []:
                parsed = self._parse_float(raw)
                if parsed is not None:
                    values.append(parsed)
        return values

    def _parse_float(self, raw: str | float | int | None) -> float | None:
        if raw is None:
            return None
        text = str(raw).strip().replace(",", "")
        if not text or text == ".":
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _keyword_signal_counts(self, text: str) -> dict[str, int]:
        buckets = {
            "profit_positive": ["profit", "ebitda", "pat", "return on assets", "roe", "growth", "margin"],
            "liquidity_positive": ["cash", "liquidity", "collections", "receivables", "operating cash"],
            "debt_negative": ["debt", "borrowing", "liability", "gearing", "leverage"],
            "governance_positive": ["board", "audit committee", "csr", "esg", "governance", "compliance"],
            "risk_negative": ["default", "npa", "fraud", "overdue", "litigation", "qualified opinion", "going concern"],
            "gst_positive": ["gst", "gstr", "2a", "2b", "3b", "input tax credit"],
            "bank_positive": ["bank", "statement", "account", "repayment", "deposits"],
            "stress_negative": ["rbi", "headwind", "stress", "downgrade", "restructuring", "wilful default"],
        }
        counts: dict[str, int] = {}
        for label, needles in buckets.items():
            counts[label] = sum(text.count(needle) for needle in needles)
        return counts

    def _identifier_hit_ratio(self, structured_documents: list[dict]) -> float:
        hits = 0
        total = 0
        for structured in structured_documents:
            for key in ("cin", "pan", "gstin"):
                total += 1
                if structured.get(key):
                    hits += 1
        if total == 0:
            return 0.0
        return min(hits / total * 2, 1.0)

    def _gst_signal_score(self, text: str, structured_documents: list[dict]) -> float:
        gst_ids = sum(1 for structured in structured_documents if structured.get("gstin"))
        has_recon_keywords = any(token in text for token in ("gstr-2a", "gstr-2b", "gstr-3b", "gst"))
        suspicious_terms = sum(text.count(term) for term in ("circular trading", "inflated turnover", "bogus", "mismatch"))
        base = 0.42 + min(gst_ids * 0.18, 0.24) + (0.12 if has_recon_keywords else 0.0)
        penalty = min(suspicious_terms * 0.12, 0.3)
        return max(0.08, min(0.95, base - penalty))

    def _cash_flow_signal_score(self, text: str, keyword_counts: dict[str, int], percentages: list[float], amount_diversity: float) -> float:
        liquidity_mentions = keyword_counts["liquidity_positive"] + keyword_counts["bank_positive"]
        positive = min(liquidity_mentions * 0.03, 0.24)
        stability_bonus = 0.08 if any(pct > 20 for pct in percentages) else 0.0
        stress_penalty = min(keyword_counts["stress_negative"] * 0.04, 0.22)
        base = 0.44 + positive + stability_bonus + amount_diversity * 0.12
        return max(0.12, min(0.94, base - stress_penalty))

    def _profitability_signal_score(self, text: str, keyword_counts: dict[str, int], percentages: list[float], risk_flags: list[str]) -> float:
        profit_mentions = keyword_counts["profit_positive"]
        positive = min(profit_mentions * 0.035, 0.28)
        margin_bonus = 0.1 if any(8 <= pct <= 40 for pct in percentages) else 0.0
        negative_flags = sum(1 for flag in risk_flags if any(term in flag.lower() for term in ("default", "npa", "going concern", "fraud")))
        penalty = min(negative_flags * 0.08, 0.28)
        base = 0.4 + positive + margin_bonus
        return max(0.1, min(0.95, base - penalty))

    def _leverage_signal_score(
        self,
        text: str,
        keyword_counts: dict[str, int],
        risk_flags: list[str],
        derived_exposure: float,
        requested_amount: float,
    ) -> float:
        debt_mentions = keyword_counts["debt_negative"]
        base = 0.66 - min(debt_mentions * 0.025, 0.2)
        exposure = requested_amount or derived_exposure
        if exposure > 15_00_00_000:
            base -= 0.08
        if exposure > 30_00_00_000:
            base -= 0.06
        if any("related party" in flag.lower() for flag in risk_flags):
            base -= 0.05
        return max(0.12, min(0.9, base))

    def _litigation_signal_score(
        self, risk_flags: list[str], litigation_hits: list[dict], text: str, litigation_index: float = 0.0
    ) -> float:
        base = 0.18 + min(len(litigation_hits) * 0.1, 0.2) + litigation_index * 0.45
        document_signals = sum(
            1 for flag in risk_flags if any(term in flag.lower() for term in ("litigation", "default", "fraud", "npa"))
        )
        base += min(document_signals * 0.08, 0.22)
        if "ibc" in text or "nclt" in text:
            base += 0.08
        return max(0.08, min(base, 0.95))

    def _governance_signal_score(self, text: str, keyword_counts: dict[str, int], risk_flags: list[str], officer_input: dict) -> float:
        governance_mentions = keyword_counts["governance_positive"]
        base = 0.46 + min(governance_mentions * 0.03, 0.24)
        base += float(officer_input.get("governance_score", 0.68)) * 0.18
        if any(term in text for term in ("audit committee", "esg", "assurance certificate", "board")):
            base += 0.07
        negative_flags = sum(1 for flag in risk_flags if any(term in flag.lower() for term in ("fraud", "qualified", "going concern")))
        base -= min(negative_flags * 0.09, 0.27)
        return max(0.1, min(base, 0.96))

    def _management_overlay_score(self, officer_input: dict, text: str) -> float:
        capacity_utilization = float(officer_input.get("capacity_utilization_pct", 75)) / 100
        management_quality = float(officer_input.get("management_quality", 7)) / 10
        inventory_observation = float(officer_input.get("inventory_observation", 7)) / 10
        customer_concentration = float(officer_input.get("customer_concentration", 35))
        concentration_adjustment = max(0.0, 1 - (customer_concentration / 100))
        qualitative_text_bonus = 0.04 if any(term in text for term in ("leadership", "management", "strategic initiatives")) else 0.0
        return max(
            0.0,
            min(
                (capacity_utilization * 0.35)
                + (management_quality * 0.3)
                + (inventory_observation * 0.2)
                + (concentration_adjustment * 0.15)
                + qualitative_text_bonus,
                1.0,
            ),
        )

    def _sector_headwind_score(
        self, negative_research: list[dict], text: str, risk_flags: list[str], sector_index: float = 0.0
    ) -> float:
        base = 0.3 + sector_index * 0.35 + min(len(negative_research) * 0.06, 0.18)
        if any(term in text for term in ("rbi", "liquidity risk", "stress", "regulatory", "headwind")):
            base += 0.1
        if any(term in " ".join(risk_flags).lower() for term in ("default", "npa")):
            base += 0.08
        return max(0.1, min(base, 0.92))

    def _esg_signal_score(self, sustainability_docs: list[dict], text: str) -> float:
        if not sustainability_docs and not any(term in text for term in ("sustainability", "esg", "gri", "climate")):
            return 0.0
        score = 0.08 + min(len(sustainability_docs) * 0.06, 0.12)
        if "assurance certificate" in text:
            score += 0.04
        return min(score, 0.22)

    def _revenue_proxy(self, currency_values: list[float], annual_reports: list[dict]) -> float:
        if not currency_values:
            return 0.0
        filtered = [value for value in currency_values if value > 50]
        if not filtered:
            return 0.0
        scale = 1.0 if annual_reports else 0.5
        return mean(sorted(filtered, reverse=True)[: min(len(filtered), 8)]) * scale

    def _liquidity_proxy(self, currency_values: list[float], text: str) -> float:
        if not currency_values:
            return 0.0
        liquidity_mentions = sum(text.count(term) for term in ("cash", "liquidity", "reserves", "balance"))
        base = mean(sorted(currency_values, reverse=True)[: min(len(currency_values), 5)]) * 0.35
        return base * min(1 + liquidity_mentions * 0.05, 1.4)
