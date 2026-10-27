from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from app import create_app
from app.config import Config
from app.ml.pd_model import PDModel
from app.services.ocr_service import OCRService
from synthetic_data.generator import generate_all


def pytest_addoption(parser):
    parser.addoption("--update-golden", action="store_true", default=False,
                     help="rewrite tests/regression/golden/*.json from the current pipeline output")


def pytest_collection_modifyitems(config, items):
    """Directory-based default markers, so `pytest -m unit` etc. work without decorating every test."""
    for item in items:
        parts = Path(str(item.fspath)).parts
        for marker in ("unit", "integration", "e2e", "regression", "security"):
            if marker in parts:
                item.add_marker(getattr(pytest.mark, marker))


@pytest.fixture(scope="session")
def update_golden(request) -> bool:
    return request.config.getoption("--update-golden")


@pytest.fixture(scope="session")
def ocr_available() -> bool:
    return OCRService().engine_name == "rapidocr"


@pytest.fixture
def requires_ocr(ocr_available):
    if not ocr_available:
        pytest.skip("RapidOCR engine not installed")


@pytest.fixture(scope="session")
def synthetic_data(tmp_path_factory) -> dict:
    root = tmp_path_factory.mktemp("synthetic")
    manifest = generate_all(root, seed=7)
    manifest["root"] = str(root)
    return manifest


@pytest.fixture(scope="session")
def pd_model() -> PDModel:
    model = PDModel.try_load(Config.PD_MODEL_DIR)
    if model is None:
        pytest.skip("PD model artifacts missing: run `python -m app.ml.train_pd_model`")
    return model


def make_app(storage: Path, corpus: Path, **overrides):
    config = {
        "STORAGE_DIR": storage,
        "RESEARCH_CORPUS_PATH": corpus,
        "ENABLE_TRANSFORMER_EXPLAINABILITY": False,   # keep tests offline and fast
        "TESTING": True,
    }
    config.update(overrides)
    return create_app(config)


@pytest.fixture
def app(tmp_path, synthetic_data):
    return make_app(tmp_path / "storage", Path(synthetic_data["research_corpus"]))


@pytest.fixture
def client(app):
    return app.test_client()


def run_borrower(client, info: dict, application_overrides: dict | None = None) -> dict:
    """Create -> ingest all synthetic files -> decide; returns every response plus timings."""
    application = {**info["application"], **(application_overrides or {})}
    created = client.post("/api/v1/applications", json=application)
    assert created.status_code == 201, created.get_json()
    application_id = created.get_json()["id"]

    started = time.perf_counter()
    handles = [open(path, "rb") for path in info["files"].values()]
    try:
        ingest = client.post(
            f"/api/v1/applications/{application_id}/documents/ingest",
            data={"documents": [(handle, Path(handle.name).name) for handle in handles]},
            content_type="multipart/form-data",
        )
    finally:
        for handle in handles:
            handle.close()
    ingest_seconds = time.perf_counter() - started
    assert ingest.status_code == 200, ingest.get_json()

    started = time.perf_counter()
    decision = client.post(f"/api/v1/applications/{application_id}/decision", json={"officer_input": info["officer_input"]})
    decision_seconds = time.perf_counter() - started
    assert decision.status_code == 200, decision.get_json()
    return {
        "application_id": application_id,
        "ingest": ingest.get_json(),
        "decision": decision.get_json(),
        "timings": {"ingest_seconds": ingest_seconds, "decision_seconds": decision_seconds},
    }


@pytest.fixture(scope="session")
def borrower_results(tmp_path_factory, synthetic_data) -> dict:
    """Run the three synthetic personas once per session (OCR makes this the slow part)."""
    storage = tmp_path_factory.mktemp("pipeline-storage")
    app = make_app(storage, Path(synthetic_data["research_corpus"]))
    client = app.test_client()
    results = {slug: run_borrower(client, info) for slug, info in synthetic_data["borrowers"].items()}
    results["_app_config"] = {"CAM_DIR": str(app.config["CAM_DIR"])}
    return results


def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
