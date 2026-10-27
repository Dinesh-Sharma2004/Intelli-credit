import math

import numpy as np
import pytest

from app.ml.features import FEATURE_KEYS, MODEL_FEATURES, feature_row
from app.ml.pd_model import PDModel
from app.ml.synthetic_training import generate_training_data
from app.ml.train_pd_model import expected_calibration_error, ks_statistic, train


def typical_features() -> dict:
    return {feature.key: feature.typical for feature in MODEL_FEATURES}


def test_feature_row_order_and_missing_defaults():
    row = feature_row({"litigation_risk_score": 0.7})
    assert len(row) == len(FEATURE_KEYS)
    assert row[FEATURE_KEYS.index("litigation_risk_score")] == 0.7
    assert row[FEATURE_KEYS.index("gst_reconciliation_risk")] == 0.0


def test_synthetic_population_is_deterministic_and_calibrated():
    X1, y1 = generate_training_data(n=3000, seed=3)
    X2, y2 = generate_training_data(n=3000, seed=3)
    assert np.array_equal(X1, X2) and np.array_equal(y1, y2)
    assert X1.shape == (3000, len(FEATURE_KEYS))
    assert X1.min() >= 0.0 and X1.max() <= 1.0
    assert 0.07 <= y1.mean() <= 0.13                    # targeted 10% default rate


def test_predictions_are_probabilities(pd_model):
    X, _ = generate_training_data(n=500, seed=11)
    probs = pd_model.predict_many(X)
    assert np.all((probs > 0) & (probs < 1))


def test_treeshap_values_sum_to_model_margin(pd_model):
    rng = np.random.default_rng(0)
    for _ in range(25):
        features = {key: float(rng.uniform(0, 1)) for key in FEATURE_KEYS}
        explanation = pd_model.explain(features)
        margin = explanation["base_value"] + sum(explanation["shap_values"].values())
        assert margin == pytest.approx(explanation["margin"], abs=1e-6)
        assert 1 / (1 + math.exp(-margin)) == pytest.approx(explanation["probability_of_default"], abs=1e-5)


def test_treeshap_agrees_with_shap_library(pd_model):
    """Cross-check against the `shap` package.

    XGBoost's native TreeSHAP is exactly additive to the booster margin; shap 0.51 re-parses
    XGBoost 3.x models slightly differently (its values do not sum to the true margin), so we
    require close agreement and the same dominant driver rather than equality.
    """
    shap = pytest.importorskip("shap")
    try:
        explainer = shap.TreeExplainer(pd_model.booster)
    except Exception as exc:  # version mismatch between shap and xgboost
        pytest.skip(f"shap cannot load this booster: {exc}")
    features = typical_features() | {"litigation_risk_score": 0.8, "gst_reconciliation_risk": 0.6}
    explanation = pd_model.explain(features)
    ours = np.array([explanation["shap_values"][k] for k in FEATURE_KEYS])
    theirs = explainer.shap_values(np.array([feature_row(features)]))[0]
    assert np.max(np.abs(ours - theirs)) < 0.1 * np.max(np.abs(ours))   # observed ~6% on one feature
    assert np.argmax(np.abs(ours)) == np.argmax(np.abs(theirs))      # same dominant driver
    assert np.corrcoef(ours, theirs)[0, 1] > 0.99                     # near-ties may reorder
    assert explanation["base_value"] == pytest.approx(float(explainer.expected_value), abs=1e-3)


@pytest.mark.parametrize("feature", MODEL_FEATURES, ids=lambda f: f.key)
def test_monotone_constraints_hold(pd_model, feature):
    """Raising a risk feature never lowers PD; raising a strength never raises it."""
    rng = np.random.default_rng(FEATURE_KEYS.index(feature.key))
    for _ in range(30):
        base = {key: float(rng.uniform(0, 1)) for key in FEATURE_KEYS}
        low = pd_model.predict(base | {feature.key: 0.1})
        high = pd_model.predict(base | {feature.key: 0.9})
        if feature.direction > 0:
            assert high >= low - 1e-9
        else:
            assert high <= low + 1e-9


def test_risk_profiles_are_ordered(pd_model):
    healthy = typical_features() | {"litigation_risk_score": 0.1, "anomaly_score": 0.0, "cash_flow_stability_score": 0.85, "profitability_score": 0.85}
    stressed = typical_features() | {"litigation_risk_score": 0.85, "anomaly_score": 0.8, "gst_reconciliation_risk": 0.8, "cash_flow_stability_score": 0.3}
    assert pd_model.predict(healthy) < pd_model.predict(typical_features()) < pd_model.predict(stressed)


def test_metric_helpers():
    y = np.array([0, 0, 1, 1])
    assert ks_statistic(y, np.array([0.1, 0.2, 0.8, 0.9])) == pytest.approx(1.0)
    assert expected_calibration_error(np.array([0, 1] * 50), np.full(100, 0.5)) == pytest.approx(0.0, abs=1e-9)


def test_training_is_reproducible_and_loadable(tmp_path):
    first = train(n=1500, seed=5, out_dir=tmp_path / "a")
    second = train(n=1500, seed=5, out_dir=tmp_path / "b")
    assert first["metrics"] == second["metrics"]
    model_a, model_b = PDModel.load(tmp_path / "a"), PDModel.load(tmp_path / "b")
    X, _ = generate_training_data(n=200, seed=99)
    assert np.allclose(model_a.predict_many(X), model_b.predict_many(X))
    assert first["feature_keys"] == FEATURE_KEYS


def test_try_load_returns_none_when_artifacts_missing(tmp_path):
    assert PDModel.try_load(tmp_path) is None
    assert PDModel.try_load(None) is None


def test_schema_mismatch_is_rejected(pd_model):
    with pytest.raises(ValueError):
        PDModel(pd_model.booster, {"feature_keys": ["something_else"]})
