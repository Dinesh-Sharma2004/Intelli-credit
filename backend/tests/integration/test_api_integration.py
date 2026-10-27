import json
from io import BytesIO
from pathlib import Path


def create(client, **overrides):
    payload = {"borrower_name": "Acme Foods Private Limited", "sector": "food processing", "requested_amount": 5e7} | overrides
    response = client.post("/api/v1/applications", json=payload)
    return response


def test_root_and_health_report_models(client):
    root = client.get("/").get_json()
    assert root["version"] == "2.1.0"
    assert root["models"]["ocr_engine"] in {"rapidocr", "none"}
    assert root["models"]["research_documents"] > 0
    assert client.get("/api/v1/health").get_json()["status"] == "healthy"


def test_create_application_validates_borrower_name(client):
    assert create(client, borrower_name="").status_code == 400
    response = create(client)
    assert response.status_code == 201
    assert response.get_json()["external_id"].startswith("APP-")


def test_unknown_application_returns_404(client):
    assert client.get("/api/v1/applications/9999").status_code == 404
    assert client.post("/api/v1/applications/9999/decision", json={}).status_code == 404
    response = client.post(
        "/api/v1/applications/9999/documents/ingest",
        data={"documents": (BytesIO(b"x"), "notes.txt")}, content_type="multipart/form-data",
    )
    assert response.status_code == 404


def test_unsupported_upload_returns_400(client):
    application_id = create(client).get_json()["id"]
    response = client.post(
        f"/api/v1/applications/{application_id}/documents/ingest",
        data={"documents": (BytesIO(b"MZ..."), "payload.exe")}, content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.get_json()["error"]


def test_ingest_by_server_path(client, synthetic_data):
    files = synthetic_data["borrowers"]["sunrise-agro"]["files"]
    application_id = create(client).get_json()["id"]
    response = client.post(f"/api/v1/applications/{application_id}/documents/ingest",
                           json={"filepaths": [files["gst_returns"], files["bank_statement"]]})
    assert response.status_code == 200
    body = response.get_json()
    assert body["summary"]["document_mix"] == {"gst_filing": 1, "bank_statement": 1}
    missing = client.post(f"/api/v1/applications/{application_id}/documents/ingest", json={"filepaths": ["C:/nope/missing.pdf"]})
    assert missing.status_code == 400


def test_cockpit_requires_decision_then_reflects_scorecard(client, synthetic_data):
    info = synthetic_data["borrowers"]["sunrise-agro"]
    application_id = create(client, **info["application"]).get_json()["id"]
    client.post(f"/api/v1/applications/{application_id}/documents/ingest",
                json={"filepaths": [info["files"]["gst_returns"], info["files"]["bank_statement"], info["files"]["annual_report"]]})
    assert client.get(f"/api/v1/applications/{application_id}/cockpit").status_code == 404

    decision = client.post(f"/api/v1/applications/{application_id}/decision", json={"officer_input": info["officer_input"]}).get_json()
    cockpit = client.get(f"/api/v1/applications/{application_id}/cockpit").get_json()
    assert cockpit["pd_meter"]["probability_of_default"] == decision["scorecard"]["probability_of_default"]
    assert {row["dimension"] for row in cockpit["risk_heatmap"]} == {"Character", "Capacity", "Capital", "Collateral", "Conditions"}

    snapshot = client.get(f"/api/v1/applications/{application_id}").get_json()
    assert snapshot["application"]["status"] == "decision_ready"
    assert snapshot["scorecard"]["explanation_method"] == "xgboost-treeshap"
    assert len(snapshot["research_hits"]) == 5
    assert snapshot["anomaly_result"]["gst_reconciliation"]["summary"]["periods_analysed"] == 12


def test_rerunning_decision_replaces_previous_results(client, synthetic_data):
    info = synthetic_data["borrowers"]["sunrise-agro"]
    application_id = create(client, **info["application"]).get_json()["id"]
    client.post(f"/api/v1/applications/{application_id}/documents/ingest", json={"filepaths": [info["files"]["gst_returns"]]})
    for _ in range(2):
        client.post(f"/api/v1/applications/{application_id}/decision", json={"officer_input": info["officer_input"]})
    snapshot = client.get(f"/api/v1/applications/{application_id}").get_json()
    assert len(snapshot["research_hits"]) == 5 and len(snapshot["compliance_checks"]) == 5


def test_cam_download_by_application(client, synthetic_data):
    info = synthetic_data["borrowers"]["sunrise-agro"]
    application_id = create(client, **info["application"]).get_json()["id"]
    assert client.get(f"/api/v1/applications/{application_id}/cam/pdf").status_code == 404
    client.post(f"/api/v1/applications/{application_id}/documents/ingest", json={"filepaths": [info["files"]["gst_returns"]]})
    decision = client.post(f"/api/v1/applications/{application_id}/decision", json={}).get_json()
    pdf = client.get(f"/api/v1/applications/{application_id}/cam/pdf")
    assert pdf.status_code == 200 and pdf.data.startswith(b"%PDF")
    assert client.get(f"/api/v1/applications/{application_id}/cam/docx").status_code == 200
    assert client.get(f"/api/v1/applications/{application_id}/cam/exe").status_code == 400
    legacy = client.get("/api/v1/cams/download", query_string={"path": decision["cam_artifact"]["pdf_path"]})
    assert legacy.status_code == 200


def test_schema_endpoints(client):
    schema = client.get("/api/v1/schema/processing").get_json()
    assert "gst_consistency_score" in schema["feature_vector"]
    matrix = client.post("/api/v1/schema/compliance-matrix", json={"document_names": ["gstr-3b.csv"]}).get_json()
    assert matrix[0]["document_type"] == "gst_filing"
