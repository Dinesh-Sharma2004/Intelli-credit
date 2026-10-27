from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

from .features import FEATURE_KEYS, FEATURE_LABELS, feature_row


logger = logging.getLogger(__name__)

MODEL_FILENAME = "pd_xgb.json"
METADATA_FILENAME = "pd_model_metadata.json"


class PDModel:
    """Trained XGBoost probability-of-default model with exact TreeSHAP attributions.

    Attributions come from XGBoost's built-in TreeSHAP (``pred_contribs=True``): for every
    prediction, base_value + sum(shap_values) equals the model margin (log-odds) exactly.
    """

    def __init__(self, booster, metadata: dict):
        self.booster = booster
        self.metadata = metadata
        if metadata.get("feature_keys") and metadata["feature_keys"] != FEATURE_KEYS:
            raise ValueError("PD model feature schema does not match app.ml.features.MODEL_FEATURES")

    @property
    def version(self) -> str:
        return self.metadata.get("model_version", "xgboost-pd")

    @classmethod
    def load(cls, model_dir: Path) -> "PDModel":
        import xgboost as xgb

        booster = xgb.Booster()
        booster.load_model(str(Path(model_dir) / MODEL_FILENAME))
        metadata = json.loads((Path(model_dir) / METADATA_FILENAME).read_text(encoding="utf-8"))
        return cls(booster, metadata)

    @classmethod
    def try_load(cls, model_dir: Path | None) -> "PDModel | None":
        if model_dir is None or not (Path(model_dir) / MODEL_FILENAME).exists():
            logger.warning("PD model artifacts not found in %s; using heuristic scorecard", model_dir)
            return None
        try:
            return cls.load(Path(model_dir))
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Could not load PD model (%s); using heuristic scorecard", exc)
            return None

    def _matrix(self, rows: list[list[float]]):
        import xgboost as xgb

        return xgb.DMatrix(np.asarray(rows, dtype=float), feature_names=FEATURE_KEYS)

    def predict(self, features: dict) -> float:
        return float(self.booster.predict(self._matrix([feature_row(features)]))[0])

    def predict_many(self, rows: np.ndarray) -> np.ndarray:
        return self.booster.predict(self._matrix(rows.tolist()))

    def explain(self, features: dict) -> dict:
        matrix = self._matrix([feature_row(features)])
        probability = float(self.booster.predict(matrix)[0])
        contributions = self.booster.predict(matrix, pred_contribs=True)[0]
        shap_values = {key: float(value) for key, value in zip(FEATURE_KEYS, contributions[:-1])}
        base_value = float(contributions[-1])
        return {
            "probability_of_default": probability,
            "base_value": base_value,
            "margin": base_value + sum(shap_values.values()),
            "shap_values": shap_values,
            "feature_values": {key: value for key, value in zip(FEATURE_KEYS, feature_row(features))},
            "labels": FEATURE_LABELS,
        }
