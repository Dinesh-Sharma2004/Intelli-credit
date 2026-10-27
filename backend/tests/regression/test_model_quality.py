"""Model-quality regression: the shipped PD model must keep its discrimination and calibration."""
import json

import numpy as np
import pytest
from sklearn.metrics import brier_score_loss, roc_auc_score

from app.config import Config
from app.ml.features import FEATURE_KEYS, MONOTONE_CONSTRAINTS
from app.ml.pd_model import METADATA_FILENAME
from app.ml.synthetic_training import generate_training_data
from app.ml.train_pd_model import expected_calibration_error, ks_statistic

MIN_AUC = 0.78
MIN_KS = 0.40
MAX_ECE = 0.05
MAX_BRIER = 0.09


@pytest.fixture(scope="module")
def metadata():
    return json.loads((Config.PD_MODEL_DIR / METADATA_FILENAME).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fresh_holdout():
    return generate_training_data(n=6000, seed=2024)      # a different draw from the training population


def test_artifact_metadata_is_consistent(pd_model, metadata):
    assert metadata["feature_keys"] == FEATURE_KEYS
    assert metadata["monotone_constraints"] == list(MONOTONE_CONSTRAINTS)
    assert metadata["model_version"] == pd_model.version
    assert metadata["metrics"]["test_roc_auc"] >= MIN_AUC


def test_discrimination_on_fresh_holdout(pd_model, fresh_holdout):
    X, y = fresh_holdout
    probs = pd_model.predict_many(X)
    assert roc_auc_score(y, probs) >= MIN_AUC
    assert ks_statistic(y, probs) >= MIN_KS


def test_calibration_on_fresh_holdout(pd_model, fresh_holdout):
    X, y = fresh_holdout
    probs = pd_model.predict_many(X)
    assert expected_calibration_error(y, probs) <= MAX_ECE
    assert brier_score_loss(y, probs) <= MAX_BRIER
    assert abs(probs.mean() - y.mean()) < 0.02            # portfolio-level PD matches the default rate


def test_served_model_reproduces_recorded_test_metrics(pd_model, metadata):
    """The artifact the backend loads must be exactly the model the metrics were computed on
    (guards against serving all boosted rounds instead of the early-stopped best iteration)."""
    from sklearn.model_selection import train_test_split

    assert pd_model.booster.num_boosted_rounds() == metadata["n_trees"] == metadata["metrics"]["best_iteration"] + 1
    training = metadata["training"]
    X, y = generate_training_data(n=training["n"], seed=training["seed"])
    _, X_temp, _, y_temp = train_test_split(X, y, test_size=0.3, random_state=training["seed"], stratify=y)
    _, X_test, _, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=training["seed"], stratify=y_temp)
    probs = pd_model.predict_many(X_test)
    assert roc_auc_score(y_test, probs) == pytest.approx(metadata["metrics"]["test_roc_auc"], abs=1e-4)
    assert brier_score_loss(y_test, probs) == pytest.approx(metadata["metrics"]["test_brier"], abs=1e-4)


def test_metrics_match_recorded_training_metrics(pd_model, metadata, fresh_holdout):
    X, y = fresh_holdout
    auc = roc_auc_score(y, pd_model.predict_many(X))
    assert auc == pytest.approx(metadata["metrics"]["test_roc_auc"], abs=0.04)


def test_pd_is_stable_for_reference_borrowers(pd_model):
    """Fixed reference rows act as a canary for accidental model replacement."""
    reference = np.array([
        [0.9, 0.9, 0.9, 0.85, 0.85, 0.8, 0.9, 0.85, 0.1, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.6, 0.5, 0.6, 0.5, 0.5, 0.5, 0.6, 0.6, 0.5, 0.6, 0.2, 0.3, 0.4, 0.5, 0.3],
        [0.5, 0.3, 0.3, 0.3, 0.3, 0.3, 0.4, 0.3, 0.9, 0.9, 0.5, 0.8, 0.9, 0.8, 0.8],
    ])
    probs = pd_model.predict_many(reference)
    assert probs[0] < 0.05 and 0.05 < probs[1] < 0.5 and probs[2] > 0.4
    assert list(probs) == sorted(probs)
