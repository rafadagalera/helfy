"""Seed de alimentos básicos e receitas pré-cadastradas (spec §5). Idempotente por nome."""
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from core_api.db.models import Food, Recipe, RecipeIngredient

SEEDS_DIR = Path(__file__).parents[2] / "seeds"


def run_seed(db: Session) -> None:
    foods_data = json.loads((SEEDS_DIR / "foods.json").read_text(encoding="utf-8"))
    recipes_data = json.loads((SEEDS_DIR / "recipes.json").read_text(encoding="utf-8"))

    foods_by_key: dict[str, Food] = {}
    for entry in foods_data:
        food = db.scalar(select(Food).where(Food.name == entry["name"]))
        if food is None:
            food = Food(name=entry["name"], food_group=entry["food_group"],
                        nutrition=entry["nutrition"],
                        allergen_flags=entry["allergen_flags"],
                        flags=entry["flags"], source="SEED")
            db.add(food)
            db.flush()
        foods_by_key[entry["key"]] = food

    for entry in recipes_data:
        if db.scalar(select(Recipe).where(Recipe.name == entry["name"])) is not None:
            continue
        recipe = Recipe(name=entry["name"], instructions=entry["instructions"],
                        nutrition_total={})
        db.add(recipe)
        db.flush()
        for ing in entry["ingredients"]:
            db.add(RecipeIngredient(recipe_id=recipe.id,
                                    food_id=foods_by_key[ing["food"]].id,
                                    quantity=ing["quantity"]))
    db.commit()


if __name__ == "__main__":
    from core_api.db.session import SessionLocal

    with SessionLocal() as session:
        run_seed(session)
        print("seed ok")
