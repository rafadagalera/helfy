"""
Heurística de score (replicada do chall-ia) e breakdown de explicabilidade.

A heurística é o ground truth do modelo MLP e o fallback em runtime.
O breakdown alimenta a transparência de resultado (SCRUM-19).
"""
import pandas as pd

# Re-export: a função canônica vive no pipeline de dados replicado (DRY)
from score_engine.data.generate_pairs import compute_score  # noqa: F401

from score_engine.mapping.profile import VALID_ALLERGENS as ALLERGENS


def build_breakdown(ind: pd.Series, food: pd.Series, heuristic_score: float) -> dict:
    """Explica o score de um par (portado de chall-ia src/api/main.py:_build_breakdown)."""
    hits = [a for a in ALLERGENS
            if ind.get(f"allergy_{a}", 0) and food.get(f"contains_{a}", 0)]
    allergen_safe = len(hits) == 0

    diet = ind.get("diet_type", "")
    diet_compat = True
    if diet == "vegan" and food.get("is_animal_product", 0):
        diet_compat = False
    elif diet == "vegetarian" and (food.get("is_meat", 0) or food.get("is_fish", 0)):
        diet_compat = False
    elif diet == "pescatarian" and food.get("is_meat", 0):
        diet_compat = False

    goal = ind.get("goal", "")
    protein = food.get("proteins_100g", 0)
    energy = food.get("energy_kcal_100g", 0)
    fiber = food.get("fiber_100g", 0)
    if goal == "muscle_gain" and protein >= 20:
        goal_alignment = "high"
    elif goal == "weight_loss" and energy < 200 and fiber > 3:
        goal_alignment = "high"
    elif goal == "health_improvement" and food.get("food_group") in ("vegetable", "fruit", "legume"):
        goal_alignment = "high"
    elif heuristic_score >= 7:
        goal_alignment = "moderate"
    elif heuristic_score >= 4:
        goal_alignment = "low"
    else:
        goal_alignment = "poor"

    flags: list[str] = []
    sodium = food.get("sodium_mg_100g", 0)
    sugar = food.get("sugar_100g", 0)
    sat_fat = food.get("saturated_fat_100g", 0)
    if ind.get("hypertension", "none") != "none" and sodium > 200:
        flags.append(f"sodium: caution ({sodium:.0f} mg/100g)")
    if ind.get("glycemic_condition", "none") != "none" and sugar > 8:
        flags.append(f"sugar: caution ({sugar:.1f} g/100g)")
    if ind.get("total_cholesterol", 0) > 240 and sat_fat > 5:
        flags.append(f"saturated fat: caution ({sat_fat:.1f} g/100g)")

    return {
        "allergen_safe": allergen_safe,
        "diet_compatible": diet_compat,
        "goal_alignment": goal_alignment,
        "health_flags": flags,
        "heuristic_reference": round(heuristic_score, 2),
    }
