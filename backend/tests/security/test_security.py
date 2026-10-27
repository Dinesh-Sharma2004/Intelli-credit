from io import BytesIO
from pathlib import Path

import pytest

from app.routes import resolve_cam_file


@pytest.fixture
def cam_dir(app):
    path = Path(app.config["CAM_DIR"])
    (path / "CAM_demo.pdf").write_bytes(b"%PDF-1.4 demo")
    (path / "notes.txt").write_text("not a CAM", encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "requested",
    [
        "../intelli_credit.db",
        "..\\intelli_credit.db",
        "../../app/config.py",
        "C:/Windows/win.ini",
        "/etc/passwd",
        "notes.txt",          # inside CAM dir but not a CAM document type
        ".",
        "",
    ],
)
def test_cam_download_rejects_paths_outside_cam_documents(client, cam_dir, requested):
    response = client.get("/api/v1/cams/download", query_string={"path": requested})
    assert response.status_code in {400, 403}
    assert b"SQLite" not in response.data


def test_absolute_path_to_database_is_denied(client, app, cam_dir):
    database = Path(app.config["STORAGE_DIR"]) / "intelli_credit.db"
    assert database.exists()
    response = client.get("/api/v1/cams/download", query_string={"path": str(database)})
    assert response.status_code == 403


def test_legitimate_cam_file_is_served(client, cam_dir):
    by_name = client.get("/api/v1/cams/download", query_string={"path": "CAM_demo.pdf"})
    by_absolute = client.get("/api/v1/cams/download", query_string={"path": str(cam_dir / "CAM_demo.pdf")})
    assert by_name.status_code == by_absolute.status_code == 200
    assert by_name.data.startswith(b"%PDF")


def test_resolve_cam_file_unit(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"x")
    assert resolve_cam_file(tmp_path, "a.pdf") == (tmp_path / "a.pdf").resolve()
    assert resolve_cam_file(tmp_path, "../a.pdf") is None
    assert resolve_cam_file(tmp_path, str(tmp_path)) is None


def test_upload_filename_traversal_is_neutralised(client, app):
    application_id = client.post("/api/v1/applications", json={"borrower_name": "Acme"}).get_json()["id"]
    response = client.post(
        f"/api/v1/applications/{application_id}/documents/ingest",
        data={"documents": (BytesIO(b"text"), "../../../escape-annual-report.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    stored = Path(response.get_json()["documents"][0]["source_path"])
    assert stored.parent.resolve() == Path(app.config["UPLOAD_DIR"]).resolve()


def test_oversized_upload_is_rejected(client, app):
    app.config["MAX_CONTENT_LENGTH"] = 1024
    application_id = client.post("/api/v1/applications", json={"borrower_name": "Acme"}).get_json()["id"]
    response = client.post(
        f"/api/v1/applications/{application_id}/documents/ingest",
        data={"documents": (BytesIO(b"x" * 4096), "big.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 413
