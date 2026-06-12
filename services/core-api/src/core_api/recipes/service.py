"""
Sugestão determinística de receitas (SCRUM-24, spec §5).

Regras: cobertura de ingredientes na dispensa >= 70%; ordenação por
(score médio desc, cobertura desc, nome asc) — ordem total estável.
Engine indisponível → degrada para (cobertura desc, nome asc) com scored=False.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core_api.db.models import Food, PantryItem, Profile, Recipe
from core_api.scoring.engine_client import EngineUnavailableError
from core_api.scoring.service import get_scores

COVERAGE_THRESHOLD = 0.7


def suggest_recipes(db: Session, profile: Profile, limit: int = 10) -> dict:
    pantry_food_ids = set(db.scalars(
        select(PantryItem.food_id).where(PantryItem.user_id == profile.user_id)
    ).all())
    if not pantry_food_ids:
        return {"receitas": [], "scored": False}

    recipes = db.scalars(
        select(Recipe).options(selectinload(Recipe.ingredients))
    ).all()

    candidates = []
    for recipe in recipes:
        ingredient_ids = [ing.food_id for ing in recipe.ingredients]
        if not ingredient_ids:
            continue
        present = [fid for fid in ingredient_ids if fid in pantry_food_ids]
        coverage = len(present) / len(ingredient_ids)
        if coverage >= COVERAGE_THRESHOLD:
            candidates.append((recipe, present, ingredient_ids, coverage))

    if not candidates:
        return {"receitas": [], "scored": False}

    # Scores dos alimentos da dispensa usados pelos candidatos (cache → engine)
    scored = True
    needed_ids = {fid for _, present, _, _ in candidates for fid in present}
    foods = db.scalars(select(Food).where(Food.id.in_(needed_ids))).all()
    try:
        scores = get_scores(db, profile, foods)
    except EngineUnavailableError:
        scored = False
        scores = {}

    results = []
    for recipe, present, ingredient_ids, coverage in candidates:
        if scored and present:
            avg = round(sum(scores[str(fid)]["score"] for fid in present) / len(present), 3)
        else:
            avg = None
        missing = [str(fid) for fid in ingredient_ids if fid not in pantry_food_ids]
        results.append({
            "id": str(recipe.id), "name": recipe.name,
            "instructions": recipe.instructions,
            "coverage": round(coverage, 3), "score_medio": avg,
            "ingredientes_faltantes": sorted(missing),
        })

    if scored:
        results.sort(key=lambda r: (-r["score_medio"], -r["coverage"], r["name"]))
    else:
        results.sort(key=lambda r: (-r["coverage"], r["name"]))
    return {"receitas": results[:limit], "scored": scored}
