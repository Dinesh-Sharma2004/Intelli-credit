"""Synthetic borrower population for training and validating the PD model.

Real loan-performance data is not available in this repository, so the model is trained on a
simulated portfolio whose structure mirrors credit-risk practice:

* a latent credit-quality factor drives all "good" signals up and all "bad" signals down,
  so features are correlated the way they are in real portfolios;
* sector stress is an exogenous shock shared by sector headwinds and early warnings;
* structured GST/bank evidence (reconciliation risk) is missing for ~45% of borrowers;
* default is drawn from a logistic model with an interaction between litigation and
  transaction anomalies (fraud-like profiles) plus irreducible noise.

The intercept is solved so the simulated default rate matches a target (10% by default).
"""
from __future__ import annotations

import numpy as np

from .features import FEATURE_KEYS, MODEL_FEATURES


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _logit(p: float) -> float:
    return float(np.log(p / (1 - p)))


def generate_features(n: int, rng: np.random.Generator) -> np.ndarray:
    quality = rng.normal(size=n)
    sector_shock = rng.normal(size=n)
    columns = []
    for feature in MODEL_FEATURES:
        loading = 0.9 * (-feature.direction)       # good features rise with quality
        base = _logit(feature.typical) + loading * quality + rng.normal(0, 0.55, n)
        if feature.key in {"sector_headwind_score", "early_warning_score"}:
            base += 0.7 * sector_shock
        values = _sigmoid(base)
        if feature.key == "gst_reconciliation_risk":
            values = np.where(rng.random(n) < 0.45, 0.0, values)
        if feature.key in {"risk_flag_density", "anomaly_score", "promoter_risk_score", "early_warning_score"}:
            values = np.where(rng.random(n) < 0.25, 0.0, values)
        columns.append(np.clip(values, 0.0, 1.0))
    return np.column_stack(columns)


LINEAR_SCALE = 1.5     # standard deviation of the linear risk index in logit units
NOISE_SCALE = 1.0      # idiosyncratic risk not captured by any feature
MEASUREMENT_NOISE = 0.05


def default_logits(X: np.ndarray, rng: np.random.Generator, intercept: float = 0.0) -> np.ndarray:
    centered = X - np.array([feature.typical for feature in MODEL_FEATURES])
    weights = np.array([feature.direction * feature.weight for feature in MODEL_FEATURES])
    raw = centered @ weights
    linear = LINEAR_SCALE * (raw - raw.mean()) / raw.std()
    litigation = X[:, FEATURE_KEYS.index("litigation_risk_score")]
    anomaly = np.maximum(X[:, FEATURE_KEYS.index("anomaly_score")], X[:, FEATURE_KEYS.index("gst_reconciliation_risk")])
    interaction = 10.0 * np.maximum(litigation - 0.5, 0) * np.maximum(anomaly - 0.4, 0)
    return intercept + linear + interaction + rng.normal(0, NOISE_SCALE, len(X))


def generate_training_data(n: int = 8000, seed: int = 42, default_rate: float = 0.10) -> tuple[np.ndarray, np.ndarray]:
    """Return (observed features, default labels). Labels depend on the true features; the
    model only sees them with measurement error, as with features extracted from documents."""
    rng = np.random.default_rng(seed)
    X = generate_features(n, rng)
    observed = np.clip(X + rng.normal(0, MEASUREMENT_NOISE, X.shape), 0.0, 1.0)
    observed[X == 0.0] = 0.0                      # absent signals stay absent
    noise_rng_state = rng.bit_generator.state

    def rate_for(intercept: float) -> float:
        local = np.random.default_rng()
        local.bit_generator.state = noise_rng_state
        return float(_sigmoid(default_logits(X, local, intercept)).mean())

    low, high = -10.0, 5.0
    for _ in range(60):                               # bisection on the intercept
        mid = (low + high) / 2
        if rate_for(mid) > default_rate:
            high = mid
        else:
            low = mid
    rng.bit_generator.state = noise_rng_state
    probabilities = _sigmoid(default_logits(X, rng, (low + high) / 2))
    y = (rng.random(n) < probabilities).astype(int)
    return observed, y
