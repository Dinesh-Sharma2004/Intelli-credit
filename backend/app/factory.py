from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config
from .db import create_all, init_db
from .ml.pd_model import PDModel
from .routes import create_blueprint
from .services.anomaly_service import AnomalyService
from .services.cam_service import CamService
from .services.compliance_service import ComplianceService
from .services.document_service import DocumentProcessingService
from .services.early_warning_service import EarlyWarningService
from .services.gst_reconciliation import GSTReconciliationService
from .services.ner_service import FinancialNERService
from .services.ocr_service import OCRService
from .services.orchestrator import PipelineOrchestrator
from .services.qualitative_intelligence import QualitativeIntelligenceService
from .services.research_service import ResearchService
from .services.scoring_service import ScoringService
from .services.spark_pipeline_simulator import SparkPipelineSimulator
from .services.transformer_explainability_service import TransformerExplainabilityService


def _apply_overrides(app: Flask, overrides: dict | None) -> None:
    """Apply config overrides; a new STORAGE_DIR re-derives the upload/CAM/database paths."""
    if not overrides:
        return
    app.config.update(overrides)
    if "STORAGE_DIR" in overrides:
        storage = Path(overrides["STORAGE_DIR"])
        app.config["STORAGE_DIR"] = storage
        if "UPLOAD_DIR" not in overrides:
            app.config["UPLOAD_DIR"] = storage / "uploads"
        if "CAM_DIR" not in overrides:
            app.config["CAM_DIR"] = storage / "cams"
        if "SQLALCHEMY_DATABASE_URI" not in overrides:
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{(storage / 'intelli_credit.db').as_posix()}"


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    _apply_overrides(app, overrides)
    CORS(app)

    for directory_key in ("STORAGE_DIR", "UPLOAD_DIR", "CAM_DIR"):
        Path(app.config[directory_key]).mkdir(parents=True, exist_ok=True)

    init_db(app.config["SQLALCHEMY_DATABASE_URI"])
    create_all()

    ocr_service = OCRService(demo_mode=app.config["DEMO_MODE"], engine=app.config["OCR_ENGINE"])
    document_service = DocumentProcessingService(
        Path(app.config["UPLOAD_DIR"]),
        workers=app.config["PARALLEL_WORKERS"],
        ocr_service=ocr_service,
        ocr_confidence_threshold=app.config["OCR_CONFIDENCE_THRESHOLD"],
        enable_ocr_fallback=app.config["ENABLE_OCR_FALLBACK"],
        demo_mode=app.config["DEMO_MODE"],
        ner_service=FinancialNERService(),
        allowed_extensions=app.config["ALLOWED_EXTENSIONS"],
    )
    pd_model = PDModel.try_load(Path(app.config["PD_MODEL_DIR"]))
    research_service = ResearchService(
        workers=app.config["PARALLEL_WORKERS"],
        timeout_seconds=app.config["RESEARCH_TIMEOUT_SECONDS"],
        demo_mode=app.config["DEMO_MODE"],
        corpus_path=Path(app.config["RESEARCH_CORPUS_PATH"]),
        enable_dense=app.config["ENABLE_DENSE_RETRIEVAL"],
    )
    orchestrator = PipelineOrchestrator(
        document_service=document_service,
        research_service=research_service,
        scoring_service=ScoringService(pd_model=pd_model),
        transformer_explainability_service=TransformerExplainabilityService(
            enabled=app.config["ENABLE_TRANSFORMER_EXPLAINABILITY"]
        ),
        anomaly_service=AnomalyService(reconciliation_service=GSTReconciliationService()),
        qualitative_intelligence_service=QualitativeIntelligenceService(),
        early_warning_service=EarlyWarningService(),
        spark_pipeline_simulator=SparkPipelineSimulator(),
        compliance_service=ComplianceService(),
        cam_service=CamService(Path(app.config["CAM_DIR"])),
    )

    app.extensions["document_service"] = document_service
    app.extensions["orchestrator"] = orchestrator
    app.extensions["model_info"] = {
        "pd_model": pd_model.version if pd_model else "heuristic-fallback",
        "ocr_engine": ocr_service.engine_name,
        "research_documents": research_service.corpus_size,
        "retrieval": research_service.retrieval_method,
    }
    app.register_blueprint(create_blueprint(orchestrator))

    @app.get("/")
    def root():
        return jsonify(
            {
                "name": "Intelli-Credit Flask Backend",
                "version": "2.1.0",
                "features": [
                    "parallel document ingestion with OCR + financial NER",
                    "GST reconciliation and anomaly detection",
                    "RAG research agent over public risk signals",
                    "XGBoost probability-of-default model with TreeSHAP explanations",
                    "CAM generation",
                    "Indian regulation mapping",
                ],
                "models": app.extensions["model_info"],
            }
        )

    return app
