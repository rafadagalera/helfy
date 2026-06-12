"""Traduz o alimento Helfy (nutrition + flags) para a linha de features do modelo."""
from score_engine.features.preprocessing import FOOD_NUM
from score_engine.mapping.profile import VALID_ALLERGENS

FOOD_FLAGS = ["animal_product", "meat", "fish"]


def map_food(food: dict) -> dict:
    nutrition = food.get("nutrition") or {}
    row = {
        "food_id": food["food_id"],
        "food_group": food.get("food_group") or "other",
    }
    for col in FOOD_NUM:
        row[col] = float(nutrition.get(col) or 0.0)

    allergens = set(food.get("allergen_flags") or [])
    for allergen in VALID_ALLERGENS:
        row[f"contains_{allergen}"] = int(allergen in allergens)

    flags = set(food.get("flags") or [])
    for flag in FOOD_FLAGS:
        row[f"is_{flag}"] = int(flag in flags)
    return row
