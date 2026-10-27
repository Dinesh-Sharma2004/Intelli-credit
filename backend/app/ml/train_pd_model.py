"""Train the XGBoost probability-of-default model on the synthetic borrower population.

Usage (from backend/):
    python -m app.ml.train_pd_model                    # writes app/ml/artifacts/
    python -m app.ml.train_pd_model --out some/dir --n 4000 --export-csv data/synthetic/pd_training.csv
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .features import FEATURE_KEYS, MONOTONE_CONSTRAINTS
from .pd_model import METADATA_FILENAME, MODEL_FILENAME
from .synthetic_training import generate_training_data


DEFAULT_OUT = Path(__file__).resolve().parent / "artifacts"
PARAMS = {
    "n_estimators": 600,
    "max_depth": 3,
    "learning_rate": 0.05,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "min_child_weight": 5,
    "reg_lambda": 1.0,
    "tree_method": "hist",
    "eval_metric": "logloss",
    "early_stopping_rounds": 40,
}


def ks_statistic(y_true: np.ndarray, scores: np.ndarray) -> float:
    order = np.argsort(scores)
    y_sorted = y_true[order]
    cum_bad = np.cumsum(y_sorted) / max(y_sorted.sum(), 1)
    cum_good = np.cumsum(1 - y_sorted) / max((1 - y_sorted).sum(), 1)
    return float(np.max(np.abs(cum_bad - cum_good)))


def expected_calibration_error(y_true: np.ndarray, probs: np.ndarray, bins: int = 10) -> float:
    edges = np.quantile(probs, np.linspace(0, 1, bins + 1))
    ece = 0.0
    for low, high in zip(edges[:-1], edges[1:]):
        mask = (probs >= low) & (probs <= high)
        if mask.any():
            ece += mask.mean() * abs(y_true[mask].mean() - probs[mask].mean())
    return float(ece)


def train(n: int = 8000, seed: int = 42, out_dir: Path = DEFAULT_OUT, export_csv: Path | None = None) -> dict:
    import xgboost as xgb
    from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
    from sklearn.model_selection import train_test_split

    X, y = generate_training_data(n=n, seed=seed)
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=seed, stratify=y_temp)

    model = xgb.XGBClassifier(
        **PARAMS,
        monotone_constraints=MONOTONE_CONSTRAINTS,
        random_state=seed,
        n_jobs=1,
    )
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    test_probs = model.predict_proba(X_test)[:, 1]

    metrics = {
        "test_roc_auc": round(float(roc_auc_score(y_test, test_probs)), 4),
        "test_brier": round(float(brier_score_loss(y_test, test_probs)), 4),
        "test_log_loss": round(float(log_loss(y_test, test_probs)), 4),
        "test_ks": round(ks_statistic(y_test, test_probs), 4),
        "test_ece": round(expected_calibration_error(y_test, test_probs), 4),
        "default_rate": round(float(y.mean()), 4),
        "best_iteration": int(model.best_iteration),
    }

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Keep only the trees early stopping selected: the served Booster would otherwise use every
    # boosted round, not the best_iteration the metrics above were computed with.
    booster = model.get_booster()[: model.best_iteration + 1]
    booster.feature_names = FEATURE_KEYS
    booster.save_model(str(out_dir / MODEL_FILENAME))
    data_hash = hashlib.sha256(np.ascontiguousarray(X).tobytes() + y.tobytes()).hexdigest()[:16]
    metadata = {
        "model_version": f"xgboost-pd-synthetic-v2-{data_hash[:8]}",
        "n_trees": model.best_iteration + 1,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "xgboost_version": xgb.__version__,
        "feature_keys": FEATURE_KEYS,
        "monotone_constraints": list(MONOTONE_CONSTRAINTS),
        "params": {k: v for k, v in PARAMS.items()},
        "training": {"n": n, "seed": seed, "train": len(y_train), "validation": len(y_val), "test": len(y_test),
                     "data_sha256_16": data_hash},
        "metrics": metrics,
        "explainability": "XGBoost TreeSHAP (pred_contribs) in log-odds units",
        "caveat": "Trained on a simulated portfolio; recalibrate on real loan-performance data before production use.",
    }
    (out_dir / METADATA_FILENAME).write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    if export_csv:
        export_csv = Path(export_csv)
        export_csv.parent.mkdir(parents=True, exist_ok=True)
        with export_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(FEATURE_KEYS + ["default"])
            for row, label in zip(X, y):
                writer.writerow([round(float(v), 5) for v in row] + [int(label)])
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=8000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--export-csv", type=Path, default=None)
    args = parser.parse_args()
    metadata = train(args.n, args.seed, args.out, args.export_csv)
    print(json.dumps({"model_version": metadata["model_version"], **metadata["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
