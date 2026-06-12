"""
Obtenção de scores com cache (tabela food_scores).

Política de cache (spec §5): hit válido = entrada com computed_at dentro do TTL
de 24h. Invalidação por evento acontece no PUT /perfil. Misses (incluindo
entradas expiradas) vão em lote para a engine e fazem upsert.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from core_api.db.models import Food, FoodScore, Profile
from core_api.scoring.engine_client import EngineUnavailableError, score_foods
from core_api.settings import settings


def justification_from_breakdown(breakdown: dict) -> str:
    """Transparência de resultado (SCRUM-19) em uma frase para o usuário."""
    if not breakdown.get("allergen_safe", True):
        return "Contém alérgeno presente no seu perfil"
    if not breakdown.get("diet_compatible", True):
        return "Incompatível com a sua dieta"
    if breakdown.get("health_flags"):
        return "Atenção: " + "; ".join(breakdown["health_flags"])
    alignment = breakdown.get("goal_alignment", "moderate")
    labels = {"high": "Forte alinhamento com o seu objetivo",
              "moderate": "Alinhamento moderado com o seu objetivo",
              "low": "Baixo alinhamento com o seu objetivo",
              "poor": "Pouco recomendado para o seu objetivo"}
    return labels.get(alignment, labels["moderate"])


def get_scores(db: Session, profile: Profile, foods: list[Food]) -> dict[str, dict]:
    """Retorna {food_id(str): {"score": float, "breakdown": dict}} para todos os foods.

    Levanta EngineUnavailableError se houver miss e a engine estiver fora."""
    user_id = profile.user_id
    food_ids = [f.id for f in foods]
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.score_cache_ttl_hours)

    cached = db.execute(
        select(FoodScore).where(FoodScore.user_id == user_id,
                                FoodScore.food_id.in_(food_ids),
                                FoodScore.computed_at >= cutoff)
    ).scalars().all()
    result = {str(row.food_id): {"score": float(row.score), "breakdown": row.breakdown}
              for row in cached}

    missing = [f for f in foods if str(f.id) not in result]
    if missing:
        engine_result = score_foods(profile, missing)
        now = datetime.now(timezone.utc)
        for food in missing:
            item = engine_result["by_food"].get(str(food.id))
            if item is None:
                raise EngineUnavailableError(f"Engine did not return score for food {food.id}")
            result[str(food.id)] = {"score": item["score"], "breakdown": item["breakdown"]}
            stmt = pg_insert(FoodScore).values(
                user_id=user_id, food_id=food.id, score=item["score"],
                breakdown=item["breakdown"],
                model_version=engine_result["model_version"], computed_at=now,
            ).on_conflict_do_update(
                index_elements=[FoodScore.user_id, FoodScore.food_id],
                set_={"score": item["score"], "breakdown": item["breakdown"],
                      "model_version": engine_result["model_version"], "computed_at": now},
            )
            db.execute(stmt)
        db.commit()
    return result
