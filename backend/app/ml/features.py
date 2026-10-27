from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelFeature:
    key: str
    label: str
    direction: int      # +1: higher value -> higher PD (monotone increasing); -1: decreasing
    typical: float      # typical value produced by the feature pipeline, used for synthetic data
    weight: float       # relative importance in the synthetic data-generating process


# Order matters: it is the column order of the trained model.
MODEL_FEATURES: tuple[ModelFeature, ...] = (
    ModelFeature("document_coverage_score", "Document coverage", -1, 0.72, 0.4),
    ModelFeature("identifier_coverage_score", "Identifier coverage", -1, 0.55, 0.3),
    ModelFeature("gst_consistency_score", "GST consistency", -1, 0.68, 1.2),
    ModelFeature("cash_flow_stability_score", "Cash-flow stability", -1, 0.62, 2.0),
    ModelFeature("profitability_score", "Profitability quality", -1, 0.60, 1.6),
    ModelFeature("leverage_score", "Leverage headroom", -1, 0.58, 1.2),
    ModelFeature("governance_score", "Governance", -1, 0.72, 1.0),
    ModelFeature("management_overlay_score", "Management overlay", -1, 0.70, 0.8),
    ModelFeature("litigation_risk_score", "Litigation risk", 1, 0.32, 2.0),
    ModelFeature("sector_headwind_score", "Sector headwinds", 1, 0.45, 1.0),
    ModelFeature("risk_flag_density", "Risk-flag density", 1, 0.15, 1.4),
    ModelFeature("anomaly_score", "Anomaly score", 1, 0.20, 1.6),
    ModelFeature("promoter_risk_score", "Promoter risk", 1, 0.18, 1.0),
    ModelFeature("early_warning_score", "Early warning score", 1, 0.15, 1.4),
    ModelFeature("gst_reconciliation_risk", "GST reconciliation risk", 1, 0.15, 2.2),
)

FEATURE_KEYS: list[str] = [feature.key for feature in MODEL_FEATURES]
FEATURE_LABELS: dict[str, str] = {feature.key: feature.label for feature in MODEL_FEATURES}
MONOTONE_CONSTRAINTS: tuple[int, ...] = tuple(feature.direction for feature in MODEL_FEATURES)


def feature_row(features: dict) -> list[float]:
    """Model input row in the trained column order; missing features count as 0 (absent signal)."""
    return [float(features.get(key, 0.0) or 0.0) for key in FEATURE_KEYS]
