from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


class Config:
    SECRET_KEY = os.getenv("INTELLI_CREDIT_SECRET", "intelli-credit-dev")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    STORAGE_DIR = Path(os.getenv("INTELLI_CREDIT_STORAGE", BASE_DIR / "storage"))
    UPLOAD_DIR = STORAGE_DIR / "uploads"
    CAM_DIR = STORAGE_DIR / "cams"
    DB_PATH = STORAGE_DIR / "intelli_credit.db"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH.as_posix()}"
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
    PARALLEL_WORKERS = int(os.getenv("INTELLI_CREDIT_PARALLELISM", "4"))
    ALLOWED_EXTENSIONS = {".pdf", ".csv", ".xlsx", ".xls", ".json", ".txt", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    RESEARCH_TIMEOUT_SECONDS = int(os.getenv("INTELLI_CREDIT_RESEARCH_TIMEOUT", "8"))
    DEMO_MODE = os.getenv("INTELLI_CREDIT_DEMO_MODE", "1") == "1"
    OCR_CONFIDENCE_THRESHOLD = float(os.getenv("INTELLI_CREDIT_OCR_THRESHOLD", "0.55"))
    ENABLE_OCR_FALLBACK = os.getenv("INTELLI_CREDIT_ENABLE_OCR", "1") == "1"
    OCR_ENGINE = os.getenv("INTELLI_CREDIT_OCR_ENGINE", "auto")  # auto | rapidocr | none
    ENABLE_TRANSFORMER_EXPLAINABILITY = os.getenv("INTELLI_CREDIT_ENABLE_TRANSFORMER", "1") == "1"
    # Research agent: local corpus of public risk signals (MCA, e-Courts, news, RBI, sector notes)
    RESEARCH_CORPUS_PATH = Path(
        os.getenv("INTELLI_CREDIT_RESEARCH_CORPUS", DATA_DIR / "synthetic" / "research_corpus.jsonl")
    )
    ENABLE_DENSE_RETRIEVAL = os.getenv("INTELLI_CREDIT_DENSE_RETRIEVAL", "0") == "1"
    # Trained XGBoost probability-of-default model (see app/ml/train_pd_model.py)
    PD_MODEL_DIR = Path(os.getenv("INTELLI_CREDIT_PD_MODEL_DIR", BASE_DIR / "app" / "ml" / "artifacts"))
