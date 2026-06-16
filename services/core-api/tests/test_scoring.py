import uuid
from datetime import datetime, timedelta, timezone

import httpx
import respx
from httpx import Response

from core_api.db.models import Food, FoodScore
from core_api.settings import settings

from tests.helpers import auth_headers
from tests.test_profile import PROFILE

ENGINE_URL = f"{settings.score_engine_url}/score"


def _engine_response(food_ids, score=0.8):
    return {"scores": [{"food_id": fid, "score": score,
                        "breakdown": {"allergen_safe": True, "diet_compatible": True,
                                      "goal_alignment": "high", "health_flags": [],
                                      "heuristic_reference": 8.0}}
                       for fid in food_ids],
            "model_version": "mlp-v1", "engine": "mlp"}


def _setup_user_with_food(client, db, email="user@helfy.app"):
    headers, user_id = auth_headers(client, email=email)
    client.put(f"/perfil/{user_id}", json=PROFILE, headers=headers)
    food = Food(name="Aveia", food_group="grain",
                nutrition={"energy_kcal_100g": 389.0}, source="MANUAL")
    db.add(food)
    db.commit()
    return headers, user_id, str(food.id)


@respx.mock
def test_score_endpoint_calls_engine_and_caches(client, db):
    headers, user_id, food_id = _setup_user_with_food(client, db)
    route = respx.post(ENGINE_URL).mock(
        return_value=Response(200, json=_engine_response([food_id])))

    resp = client.post("/score", headers=headers,
                       json={"usuario_id": user_id, "alimento_ids": [food_id]})
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["alimento_id"] == food_id
    assert body[0]["score"] == 0.8
    assert isinstance(body[0]["justificativa"], str)

    # Segunda chamada: vem do cache, engine não é chamada de novo
    client.post("/score", headers=headers,
                json={"usuario_id": user_id, "alimento_ids": [food_id]})
    assert route.call_count == 1
    assert db.query(FoodScore).count() == 1


@respx.mock
def test_expired_cache_entry_is_recomputed(client, db):
    headers, user_id, food_id = _setup_user_with_food(client, db)
    stale = datetime.now(timezone.utc) - timedelta(hours=25)  # além do TTL de 24h
    db.add(FoodScore(user_id=uuid.UUID(user_id), food_id=uuid.UUID(food_id),
                     score=0.1, breakdown={}, model_version="mlp-v1", computed_at=stale))
    db.commit()

    route = respx.post(ENGINE_URL).mock(
        return_value=Response(200, json=_engine_response([food_id], score=0.9)))
    resp = client.post("/score", headers=headers,
                       json={"usuario_id": user_id, "alimento_ids": [food_id]})
    assert route.call_count == 1            # recalculou
    assert resp.json()[0]["score"] == 0.9


@respx.mock
def test_engine_down_returns_503(client, db):
    headers, user_id, food_id = _setup_user_with_food(client, db)
    respx.post(ENGINE_URL).mock(side_effect=httpx.ConnectError("connection refused"))
    resp = client.post("/score", headers=headers,
                       json={"usuario_id": user_id, "alimento_ids": [food_id]})
    assert resp.status_code == 503


@respx.mock
def test_engine_contract_error_returns_500_not_503(client, db):
    # 4xx da engine é bug de contrato, não instabilidade — não mascarar como 503
    headers, user_id, food_id = _setup_user_with_food(client, db)
    respx.post(ENGINE_URL).mock(
        return_value=Response(422, json={"detail": "validation error"}))
    resp = client.post("/score", headers=headers,
                       json={"usuario_id": user_id, "alimento_ids": [food_id]})
    assert resp.status_code == 500


def test_score_requires_profile(client, db):
    headers, user_id = auth_headers(client)
    food = Food(name="Maçã", food_group="fruit", nutrition={}, source="MANUAL")
    db.add(food)
    db.commit()
    resp = client.post("/score", headers=headers,
                       json={"usuario_id": user_id, "alimento_ids": [str(food.id)]})
    assert resp.status_code == 409  # perfil é pré-requisito para personalizar
