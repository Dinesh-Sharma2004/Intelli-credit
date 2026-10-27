from __future__ import annotations

import uuid

from ..db import session_scope
from ..models import CamArtifact, ComplianceCheck, CreditApplication, ResearchFinding, RiskScorecard, SourceDocument
from .anomaly_service import AnomalyService
from .cam_service import CamService
from .compliance_service import ComplianceService
from .document_catalog import compliance_matrix_for_documents
from .document_service import DocumentProcessingService
from .early_warning_service import EarlyWarningService
from .qualitative_intelligence import QualitativeIntelligenceService
from .research_service import ResearchService
from .scoring_service import ScoringService
from .spark_pipeline_simulator import SparkPipelineSimulator
from .transformer_explainability_service import TransformerExplainabilityService


class PipelineOrchestrator:
    def __init__(
        self,
        document_service: DocumentProcessingService,
        research_service: ResearchService,
        scoring_service: ScoringService,
        transformer_explainability_service: TransformerExplainabilityService,
        anomaly_service: AnomalyService,
        qualitative_intelligence_service: QualitativeIntelligenceService,
        early_warning_service: EarlyWarningService,
        spark_pipeline_simulator: SparkPipelineSimulator,
        compliance_service: ComplianceService,
        cam_service: CamService,
    ):
        self.document_service = document_service
        self.research_service = research_service
        self.scoring_service = scoring_service
        self.transformer_explainability_service = transformer_explainability_service
        self.anomaly_service = anomaly_service
        self.qualitative_intelligence_service = qualitative_intelligence_service
        self.early_warning_service = early_warning_service
        self.spark_pipeline_simulator = spark_pipeline_simulator
        self.compliance_service = compliance_service
        self.cam_service = cam_service

    def create_application(self, payload: dict) -> dict:
        external_id = payload.get("external_id") or f"APP-{uuid.uuid4().hex[:10].upper()}"
        with session_scope() as session:
            application = CreditApplication(
                external_id=external_id,
                borrower_name=payload["borrower_name"],
                borrower_pan=payload.get("borrower_pan"),
                borrower_gstin=payload.get("borrower_gstin"),
                cin=payload.get("cin"),
                sector=payload.get("sector"),
                requested_amount=float(payload.get("requested_amount", 0.0)),
                requested_tenor_months=int(payload.get("requested_tenor_months", 12)),
                notes=payload.get("notes"),
                status="created",
            )
            session.add(application)
            session.flush()
            return {"id": application.id, "external_id": application.external_id}

    def ingest_documents(self, application_id: int, paths: list[str] | None = None, files: list | None = None) -> dict:
        persisted = self.document_service.import_existing_paths(paths or []) if paths else self.document_service.persist_documents(files or [])
        processed_docs = self.document_service.process_documents_parallel(persisted)
        with session_scope() as session:
            application = session.get(CreditApplication, application_id)
            if application is None:
                raise LookupError(f"Application {application_id} not found")
            for doc in processed_docs:
                session.add(SourceDocument(application_id=application_id, **doc))
            application.status = "documents_ingested"
        return {
            "application_id": application_id,
            "documents": [self._serialize_ingest_document(doc) for doc in processed_docs],
            "summary": self.document_service.summarize_document_mix(processed_docs),
            "schema": self.document_service.export_processing_schema(),
            "compliance_matrix": compliance_matrix_for_documents([doc["document_name"] for doc in processed_docs]),
        }

    def run_full_pipeline(self, application_id: int, officer_input: dict | None = None) -> dict:
        with session_scope() as session:
            application = session.get(CreditApplication, application_id)
            if application is None:
                raise LookupError(f"Application {application_id} not found")
            documents = [self._serialize_document(doc) for doc in application.documents]
            application_dict = self._serialize_application(application)

        qualitative_intelligence = self.qualitative_intelligence_service.analyze(officer_input)
        research_hits = self.research_service.run_parallel_research(
            application_dict["borrower_name"], application_dict.get("sector")
        )
        research_graph = self.research_service.build_research_graph(research_hits)
        anomaly_result = self.anomaly_service.analyze(documents, application_dict)
        early_warning_result = self.early_warning_service.analyze(documents, research_hits, anomaly_result)
        compliance_checks = self.compliance_service.build_checks(
            [document["document_name"] for document in documents], research_hits, anomaly_result
        )
        scorecard = self.scoring_service.score(
            application_dict,
            documents,
            research_hits,
            officer_input,
            qualitative_intelligence,
            anomaly_result,
            research_graph,
            early_warning_result,
        )
        transformer_explainability = self.transformer_explainability_service.generate(
            documents, scorecard, research_hits
        )
        cam_artifact = self.cam_service.generate(
            application_dict,
            documents,
            research_hits,
            scorecard,
            compliance_checks,
            transformer_explainability,
            anomaly_result,
            qualitative_intelligence,
            early_warning_result,
            research_graph,
        )
        cockpit = self.build_cockpit_payload(
            application_dict,
            documents,
            scorecard,
            anomaly_result,
            early_warning_result,
            transformer_explainability,
        )
        spark_simulation = self.spark_pipeline_simulator.simulate(documents)

        with session_scope() as session:
            application = session.get(CreditApplication, application_id)
            if application is None:
                raise LookupError(f"Application {application_id} not found")
            application.research_hits.clear()
            application.compliance_checks.clear()
            if application.scorecard is not None:
                session.delete(application.scorecard)
            if application.cam_artifact is not None:
                session.delete(application.cam_artifact)
            # Flush the deletes first: the unit of work would otherwise INSERT the new
            # one-per-application scorecard/CAM before deleting the old rows (UNIQUE violation).
            session.flush()
            for hit in research_hits:
                session.add(ResearchFinding(application_id=application_id, **hit))
            for check in compliance_checks:
                session.add(ComplianceCheck(application_id=application_id, **check))
            session.add(RiskScorecard(application_id=application_id, **self._scorecard_db_payload(scorecard)))
            session.add(CamArtifact(application_id=application_id, **cam_artifact))
            application.status = "decision_ready"

        return {
            "application": application_dict,
            "documents": documents,
            "research_hits": research_hits,
            "research_graph": research_graph,
            "compliance_checks": compliance_checks,
            "scorecard": scorecard,
            "qualitative_intelligence": qualitative_intelligence,
            "anomaly_result": anomaly_result,
            "early_warning_result": early_warning_result,
            "transformer_explainability": transformer_explainability,
            "cockpit": cockpit,
            "spark_simulation": spark_simulation,
            "cam_artifact": cam_artifact,
        }

    def get_application_snapshot(self, application_id: int) -> dict:
        with session_scope() as session:
            application = session.get(CreditApplication, application_id)
            if application is None:
                raise LookupError(f"Application {application_id} not found")
            documents = [self._serialize_document(doc) for doc in application.documents]
            research_hits = [self._serialize_research(hit) for hit in application.research_hits]
            scorecard = self._serialize_scorecard(application.scorecard) if application.scorecard else None
            anomaly_result = self.anomaly_service.analyze(documents, self._serialize_application(application))
            early_warning_result = self.early_warning_service.analyze(documents, research_hits, anomaly_result)
            research_graph = self.research_service.build_research_graph(research_hits)
            transformer_explainability = (
                application.cam_artifact.memo_json.get("transformer_explainability", {})
                if application.cam_artifact and application.cam_artifact.memo_json
                else {}
            )
            return {
                "application": self._serialize_application(application),
                "documents": documents,
                "research_hits": research_hits,
                "research_graph": research_graph,
                "compliance_checks": [self._serialize_compliance(check) for check in application.compliance_checks],
                "scorecard": scorecard,
                "anomaly_result": anomaly_result,
                "early_warning_result": early_warning_result,
                "cockpit": self.build_cockpit_payload(
                    self._serialize_application(application),
                    documents,
                    scorecard or {},
                    anomaly_result,
                    early_warning_result,
                    transformer_explainability,
                ) if scorecard else None,
                "cam_artifact": self._serialize_cam(application.cam_artifact) if application.cam_artifact else None,
            }

    def get_application_cockpit(self, application_id: int) -> dict:
        snapshot = self.get_application_snapshot(application_id)
        cockpit = snapshot.get("cockpit")
        if cockpit is None:
            raise LookupError(f"Application {application_id} not ready for cockpit view")
        return cockpit

    def build_cockpit_payload(
        self,
        application: dict,
        documents: list[dict],
        scorecard: dict,
        anomaly_result: dict,
        early_warning_result: dict,
        transformer_explainability: dict,
    ) -> dict:
        document_completeness = min(len(documents) / 6, 1.0)
        feature_vector = scorecard.get("feature_vector", {})
        return {
            "borrower_name": application.get("borrower_name"),
            "pd_meter": {
                "probability_of_default": scorecard.get("probability_of_default", 0.0),
                "band": scorecard.get("pd_band", "n/a"),
                "risk_grade": scorecard.get("risk_grade", "n/a"),
            },
            "risk_heatmap": [
                {"dimension": "Character", "value": scorecard.get("score_breakdown", {}).get("character", 0.0)},
                {"dimension": "Capacity", "value": scorecard.get("score_breakdown", {}).get("capacity", 0.0)},
                {"dimension": "Capital", "value": scorecard.get("score_breakdown", {}).get("capital", 0.0)},
                {"dimension": "Collateral", "value": scorecard.get("score_breakdown", {}).get("collateral", 0.0)},
                {"dimension": "Conditions", "value": scorecard.get("score_breakdown", {}).get("conditions", 0.0)},
            ],
            "document_completeness_pct": round(document_completeness * 100, 2),
            "anomaly_alerts": anomaly_result.get("anomaly_flags", []),
            "early_warning_signals": early_warning_result.get("early_warning_flags", []),
            "sanction_simulation_bands": scorecard.get("sanction_simulation", {}),
            "feature_waterfall": scorecard.get("shap_explanation", []),
            "transformer_evidence_score": transformer_explainability.get("average_evidence_score", 0.0),
            "heatmap_inputs": {
                "litigation": feature_vector.get("litigation_risk_score", 0.0),
                "governance": feature_vector.get("governance_score", 0.0),
                "anomaly": feature_vector.get("anomaly_score", 0.0),
                "early_warning": feature_vector.get("early_warning_score", 0.0),
            },
        }

    def _serialize_application(self, application: CreditApplication) -> dict:
        return {
            "id": application.id,
            "external_id": application.external_id,
            "borrower_name": application.borrower_name,
            "borrower_pan": application.borrower_pan,
            "borrower_gstin": application.borrower_gstin,
            "cin": application.cin,
            "sector": application.sector,
            "requested_amount": application.requested_amount,
            "requested_tenor_months": application.requested_tenor_months,
            "status": application.status,
            "notes": application.notes,
        }

    def _serialize_document(self, document: SourceDocument) -> dict:
        return {
            "id": document.id,
            "document_name": document.document_name,
            "document_type": document.document_type,
            "category": document.category,
            "source_path": document.source_path,
            "language": document.language,
            "extracted_text": document.extracted_text,
            "structured_data": document.structured_data or {},
            "metadata_json": document.metadata_json or {},
            "risk_flags": document.risk_flags or [],
            "processing_status": document.processing_status,
            "confidence_score": document.confidence_score,
        }

    def _serialize_research(self, item: ResearchFinding) -> dict:
        return {
            "source_name": item.source_name,
            "title": item.title,
            "source_url": item.source_url,
            "finding_type": item.finding_type,
            "summary": item.summary,
            "sentiment": item.sentiment,
            "severity": item.severity,
            "payload": item.payload or {},
        }

    def _serialize_compliance(self, item: ComplianceCheck) -> dict:
        return {
            "regulation_code": item.regulation_code,
            "regulation_name": item.regulation_name,
            "applicability": item.applicability,
            "status": item.status,
            "rationale": item.rationale,
            "evidence": item.evidence or [],
        }

    def _serialize_scorecard(self, item: RiskScorecard) -> dict:
        payload = {
            "explanation_method": "xgboost-treeshap" if item.model_version.startswith("xgboost") else "heuristic-weights",
            "model_version": item.model_version,
            "probability_of_default": item.probability_of_default,
            "risk_grade": item.risk_grade,
            "recommended_limit": item.recommended_limit,
            "recommended_rate": item.recommended_rate,
            "decision": item.decision,
            "score_breakdown": item.score_breakdown,
            "shap_explanation": item.shap_explanation,
            "feature_vector": item.feature_vector,
            "explanation_summary": item.explanation_summary,
        }
        payload["pd_band"] = self.scoring_service.pd_band(item.probability_of_default)
        payload["risk_premium"] = self.scoring_service.risk_premium(item.probability_of_default, item.feature_vector or {})
        payload["sanction_simulation"] = self.scoring_service.sanction_simulation(
            (item.feature_vector or {}).get("derived_exposure_cr", 5.0) * 1e7,
            item.feature_vector or {},
            item.probability_of_default,
        )
        payload["scenario_analysis"] = self.scoring_service.scenario_analysis(
            (item.feature_vector or {}).get("derived_exposure_cr", 5.0) * 1e7,
            item.feature_vector or {},
            item.probability_of_default,
        )
        payload["covenant_recommendations"] = self.scoring_service.covenant_recommendations(
            item.feature_vector or {},
            {},
            {},
        )
        return payload

    def _scorecard_db_payload(self, scorecard: dict) -> dict:
        return {
            "model_version": scorecard["model_version"],
            "probability_of_default": scorecard["probability_of_default"],
            "risk_grade": scorecard["risk_grade"],
            "recommended_limit": scorecard["recommended_limit"],
            "recommended_rate": scorecard["recommended_rate"],
            "decision": scorecard["decision"],
            "score_breakdown": scorecard["score_breakdown"],
            "shap_explanation": scorecard["shap_explanation"],
            "feature_vector": scorecard["feature_vector"],
            "explanation_summary": scorecard["explanation_summary"],
        }

    def _serialize_cam(self, item: CamArtifact) -> dict:
        return {
            "docx_path": item.docx_path,
            "pdf_path": item.pdf_path,
            "memo_json": item.memo_json,
            "generation_status": item.generation_status,
        }

    def _serialize_ingest_document(self, document: dict) -> dict:
        return {
            "document_name": document.get("document_name"),
            "document_type": document.get("document_type"),
            "category": document.get("category"),
            "source_path": document.get("source_path"),
            "language": document.get("language"),
            "structured_data": {
                "document_label": (document.get("structured_data") or {}).get("document_label"),
                "page_count": ((document.get("metadata_json") or {}).get("page_count")),
                "keywords": ((document.get("structured_data") or {}).get("keywords") or [])[:8],
                "error": (document.get("structured_data") or {}).get("error"),
            },
            "risk_flags": document.get("risk_flags") or [],
            "metadata_json": {
                "extraction_source": ((document.get("metadata_json") or {}).get("extraction_source")),
                "ocr_confidence": ((document.get("metadata_json") or {}).get("ocr_confidence")),
            },
            "processing_status": document.get("processing_status"),
            "confidence_score": document.get("confidence_score"),
        }
