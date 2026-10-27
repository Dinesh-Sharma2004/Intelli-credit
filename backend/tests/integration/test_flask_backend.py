from io import BytesIO


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["framework"] == "flask"
    assert payload["models"]["pd_model"].startswith("xgboost")


def test_application_lifecycle(client):
    create_response = client.post(
        "/api/v1/applications",
        json={
            "borrower_name": "Kinara Capital",
            "sector": "NBFC",
            "requested_amount": 150000000,
            "requested_tenor_months": 36,
        },
    )
    assert create_response.status_code == 201
    application_id = create_response.get_json()["id"]

    ingest_response = client.post(
        f"/api/v1/applications/{application_id}/documents/ingest",
        data={"documents": (BytesIO(b"sample annual report"), "fy24-annual-report-kinara-capital.txt")},
        content_type="multipart/form-data",
    )
    assert ingest_response.status_code == 200
    assert ingest_response.get_json()["summary"]["document_count"] == 1

    decision_response = client.post(
        f"/api/v1/applications/{application_id}/decision",
        json={"officer_input": {"capacity_utilization_pct": 40, "governance_score": 0.62}},
    )
    assert decision_response.status_code == 200
    assert decision_response.get_json()["scorecard"]["decision"] in {"approve", "review", "reject"}
