from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file
from werkzeug.exceptions import HTTPException

from .services.document_catalog import compliance_matrix_for_documents
from .services.document_service import UnsupportedDocumentError


def resolve_cam_file(cam_dir: Path, requested: str) -> Path | None:
    """Resolve a CAM download request, refusing anything outside the CAM directory."""
    root = Path(cam_dir).resolve()
    candidate = Path(requested)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        resolved = candidate.resolve()
    except (OSError, RuntimeError):
        return None
    if not resolved.is_relative_to(root) or resolved == root:
        return None
    if resolved.suffix.lower() not in {".pdf", ".docx"}:
        return None
    return resolved


def create_blueprint(orchestrator):
    bp = Blueprint("api", __name__, url_prefix="/api/v1")

    @bp.get("/health")
    def health():
        return jsonify(
            {
                "status": "healthy",
                "framework": "flask",
                "service": "intelli-credit",
                "parallel_workers": current_app.config["PARALLEL_WORKERS"],
                "models": current_app.extensions.get("model_info", {}),
            }
        )

    @bp.post("/applications")
    def create_application():
        payload = request.get_json(force=True)
        if not str(payload.get("borrower_name") or "").strip():
            return jsonify({"error": "borrower_name is required"}), 400
        response = orchestrator.create_application(payload)
        return jsonify(response), 201

    @bp.post("/applications/<int:application_id>/documents/ingest")
    def ingest_documents(application_id: int):
        try:
            if request.files:
                files = request.files.getlist("documents")
                result = orchestrator.ingest_documents(application_id, files=files)
            else:
                payload = request.get_json(force=True)
                result = orchestrator.ingest_documents(application_id, paths=payload.get("filepaths", []))
        except LookupError as exc:
            return jsonify({"error": str(exc)}), 404
        except (UnsupportedDocumentError, FileNotFoundError) as exc:
            return jsonify({"error": str(exc)}), 400
        except HTTPException:
            raise                      # e.g. 413 Request Entity Too Large
        except Exception as exc:
            return jsonify({"error": f"Document ingestion failed: {exc}"}), 500
        return jsonify(result)

    @bp.post("/applications/<int:application_id>/decision")
    def run_decision(application_id: int):
        payload = request.get_json(silent=True) or {}
        try:
            result = orchestrator.run_full_pipeline(application_id, officer_input=payload.get("officer_input"))
        except LookupError as exc:
            return jsonify({"error": str(exc)}), 404
        return jsonify(result)

    @bp.get("/applications/<int:application_id>")
    def get_application(application_id: int):
        try:
            return jsonify(orchestrator.get_application_snapshot(application_id))
        except LookupError as exc:
            return jsonify({"error": str(exc)}), 404

    @bp.get("/applications/<int:application_id>/cockpit")
    def get_application_cockpit(application_id: int):
        try:
            return jsonify(orchestrator.get_application_cockpit(application_id))
        except LookupError as exc:
            return jsonify({"error": str(exc)}), 404

    @bp.get("/schema/processing")
    def schema():
        service = current_app.extensions["document_service"]
        return jsonify(service.export_processing_schema())

    @bp.post("/schema/compliance-matrix")
    def compliance_matrix():
        payload = request.get_json(force=True)
        return jsonify(compliance_matrix_for_documents(payload.get("document_names", [])))

    @bp.get("/cams/download")
    def download_cam():
        path = request.args.get("path")
        if not path:
            return jsonify({"error": "path query parameter is required"}), 400
        file_path = resolve_cam_file(current_app.config["CAM_DIR"], path)
        if file_path is None:
            return jsonify({"error": "access denied: only generated CAM files can be downloaded"}), 403
        if not file_path.exists():
            return jsonify({"error": "file not found"}), 404
        return send_file(file_path, as_attachment=True)

    @bp.get("/applications/<int:application_id>/cam/<fmt>")
    def download_application_cam(application_id: int, fmt: str):
        if fmt not in {"pdf", "docx"}:
            return jsonify({"error": "format must be pdf or docx"}), 400
        try:
            snapshot = orchestrator.get_application_snapshot(application_id)
        except LookupError as exc:
            return jsonify({"error": str(exc)}), 404
        cam = snapshot.get("cam_artifact") or {}
        stored = cam.get(f"{fmt}_path")
        file_path = resolve_cam_file(current_app.config["CAM_DIR"], stored) if stored else None
        if file_path is None or not file_path.exists():
            return jsonify({"error": "CAM not generated yet"}), 404
        return send_file(file_path, as_attachment=True)

    return bp
