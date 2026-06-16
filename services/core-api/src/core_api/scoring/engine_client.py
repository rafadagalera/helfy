"""Cliente HTTP da score-engine (contrato do Plano 1)."""
import logging

import httpx

from core_api.db.models import Food, Profile
from core_api.settings import settings

logger = logging.getLogger(__name__)

# Pool de conexões reutilizado entre requests (keep-alive com a engine)
_client = httpx.Client(base_url=settings.score_engine_url, timeout=30.0)


class EngineUnavailableError(Exception):
    """Engine fora do ar ou instável — o chamador degrada/retorna 503."""


class EngineContractError(Exception):
    """A engine rejeitou o payload (4xx) ou respondeu fora do contrato — bug, não instabilidade."""


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
        resp = _client.post("/score", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return {
            "by_food": {item["food_id"]: item for item in data["scores"]},
            "model_version": data["model_version"],
        }
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code < 500:
            logger.error("score-engine rejeitou o payload (%s): %s",
                         exc.response.status_code, exc.response.text)
            raise EngineContractError(exc.response.text) from exc
        raise EngineUnavailableError(str(exc)) from exc
    except (KeyError, ValueError) as exc:
        logger.error("resposta da score-engine fora do contrato: %s", exc)
        raise EngineContractError(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise EngineUnavailableError(str(exc)) from exc
