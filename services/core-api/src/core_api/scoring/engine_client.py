"""Cliente HTTP da score-engine (contrato do Plano 1)."""
import httpx

from core_api.db.models import Food, Profile
from core_api.settings import settings


class EngineUnavailableError(Exception):
    pass


def _profile_payload(profile: Profile) -> dict:
    return {
        "goal": profile.goal,
        "diet_type": profile.diet_type or "omnivore",
        "activity_level": profile.activity_level or "lightly_active",
        "age": profile.age,
        "weight_kg": profile.weight_kg,
        "height_cm": profile.height_cm,
        "total_cholesterol": profile.cholesterol,
        "glucose": profile.glucose,
        "allergies": profile.allergies or [],
        "restrictions": profile.restrictions or [],
    }


def _food_payload(food: Food) -> dict:
    return {
        "food_id": str(food.id),
        "food_group": food.food_group,
        "nutrition": food.nutrition or {},
        "allergen_flags": food.allergen_flags or [],
        "flags": food.flags or [],
    }


def score_foods(profile: Profile, foods: list[Food]) -> dict:
    """POST /score na engine. Retorna {food_id: {score, breakdown}} e a versão do modelo."""
    payload = {"profile": _profile_payload(profile),
               "foods": [_food_payload(f) for f in foods]}
    try:
        resp = httpx.post(f"{settings.score_engine_url}/score", json=payload, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise EngineUnavailableError(str(exc)) from exc
    return {
        "by_food": {item["food_id"]: item for item in data["scores"]},
        "model_version": data["model_version"],
    }
