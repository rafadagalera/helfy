import uuid

from core_api.db.models import Food, FoodScore

from tests.helpers import auth_headers

PROFILE = {
    "age": 30, "height_cm": 170.0, "weight_kg": 80.0,
    "goal": "EMAGRECER", "diet_type": "vegetarian", "activity_level": "lightly_active",
    "cholesterol": 210, "glucose": 110,
    "restrictions": ["low_sugar"], "preferences": ["doces"], "allergies": ["lactose"],
}


def test_put_creates_and_get_returns_profile(client):
    headers, user_id = auth_headers(client)
    resp = client.put(f"/perfil/{user_id}", json=PROFILE, headers=headers)
    assert resp.status_code == 200

    resp = client.get(f"/perfil/{user_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["goal"] == "EMAGRECER"
    assert body["allergies"] == ["lactose"]


def test_get_profile_before_creation_404(client):
    headers, user_id = auth_headers(client)
    assert client.get(f"/perfil/{user_id}", headers=headers).status_code == 404


def test_cannot_access_other_users_profile(client):
    headers_a, _ = auth_headers(client, email="a@helfy.app")
    _, user_b = auth_headers(client, email="b@helfy.app")
    assert client.get(f"/perfil/{user_b}", headers=headers_a).status_code == 403


def test_invalid_goal_422(client):
    headers, user_id = auth_headers(client)
    resp = client.put(f"/perfil/{user_id}", json={**PROFILE, "goal": "FICAR_FORTE"},
                      headers=headers)
    assert resp.status_code == 422


def test_put_profile_invalidates_score_cache(client, db):
    headers, user_id = auth_headers(client)
    client.put(f"/perfil/{user_id}", json=PROFILE, headers=headers)

    food = Food(name="Maçã", food_group="fruit", nutrition={}, source="MANUAL")
    db.add(food)
    db.flush()
    db.add(FoodScore(user_id=uuid.UUID(user_id), food_id=food.id,
                     score=0.9, breakdown={}, model_version="mlp-v1"))
    db.commit()

    client.put(f"/perfil/{user_id}", json={**PROFILE, "goal": "MANTER"}, headers=headers)
    assert db.query(FoodScore).filter_by(user_id=uuid.UUID(user_id)).count() == 0
