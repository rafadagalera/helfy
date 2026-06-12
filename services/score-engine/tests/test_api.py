"""Contrato HTTP da engine: /score, /health e geração do OpenAPI."""
from fastapi.testclient import TestClient

from score_engine.api.main import app
from tests.test_mapping import HELFY_FOOD, HELFY_PROFILE


def _client() -> TestClient:
    return TestClient(app)  # context manager dispara o lifespan


def test_health_reports_model_loaded():
    with _client() as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["model_version"] == "mlp-v1"


def test_score_batch_contract():
    with _client() as client:
        resp = client.post("/score", json={"profile": HELFY_PROFILE,
                                           "foods": [HELFY_FOOD]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["engine"] == "mlp"
    assert body["model_version"] == "mlp-v1"
    assert len(body["scores"]) == 1
    item = body["scores"][0]
    assert item["food_id"] == "abc-123"
    assert 0.0 <= item["score"] <= 1.0
    assert item["breakdown"]["allergen_safe"] is False  # perfil tem alergia a lactose


def test_score_rejects_empty_foods():
    with _client() as client:
        resp = client.post("/score", json={"profile": HELFY_PROFILE, "foods": []})
    assert resp.status_code == 422


def test_score_rejects_invalid_goal():
    with _client() as client:
        resp = client.post("/score", json={
            "profile": {**HELFY_PROFILE, "goal": "FICAR_FORTE"},
            "foods": [HELFY_FOOD],
        })
    assert resp.status_code == 422


def test_openapi_schema_is_generated():
    with _client() as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "/score" in schema["paths"]
    assert "/health" in schema["paths"]
    assert schema["info"]["title"] == "Helfy Score Engine"
