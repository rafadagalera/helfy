"""Heurística replicada: casos clínicos conhecidos + estrutura do breakdown."""
import pandas as pd

from score_engine.scoring import build_breakdown, compute_score
from tests.test_artifacts import SAMPLE_ROW

IND_COLS = [k for k in SAMPLE_ROW if not k.startswith(("energy", "proteins", "carbo", "fat",
            "saturated", "fiber", "sodium", "sugar", "food_group", "contains_", "is_"))]
FOOD_COLS = [k for k in SAMPLE_ROW if k not in IND_COLS]


def _ind(**overrides) -> pd.Series:
    return pd.Series({**{k: SAMPLE_ROW[k] for k in IND_COLS}, **overrides})


def _food(**overrides) -> pd.Series:
    return pd.Series({**{k: SAMPLE_ROW[k] for k in FOOD_COLS}, **overrides})


def test_allergen_zeroes_score():
    score = compute_score(_ind(allergy_nuts=1), _food(contains_nuts=1), noise_std=0.0)
    assert score == 0.0


def test_vegan_with_meat_is_penalized():
    base = compute_score(_ind(diet_type="vegan"), _food(), noise_std=0.0)
    meat = compute_score(_ind(diet_type="vegan"),
                         _food(is_animal_product=1, is_meat=1), noise_std=0.0)
    assert meat < base


def test_hypertension_with_sodium_is_penalized():
    base = compute_score(_ind(), _food(), noise_std=0.0)
    salty = compute_score(_ind(hypertension="uncontrolled"),
                          _food(sodium_mg_100g=800.0), noise_std=0.0)
    assert salty < base


def test_deterministic_without_noise():
    a = compute_score(_ind(), _food(), noise_std=0.0)
    b = compute_score(_ind(), _food(), noise_std=0.0)
    assert a == b


def test_maintenance_goal_aligns_high_with_vegetables():
    # MANTER mapeia para "maintenance" — vegetais/frutas/legumes devem alinhar "high"
    bd = build_breakdown(_ind(goal="maintenance"), _food(food_group="vegetable"),
                         heuristic_score=6.0)
    assert bd["goal_alignment"] == "high"


def test_breakdown_structure():
    bd = build_breakdown(_ind(allergy_nuts=1), _food(contains_nuts=1), heuristic_score=0.0)
    assert bd["allergen_safe"] is False
    assert set(bd) == {"allergen_safe", "diet_compatible", "goal_alignment",
                       "health_flags", "heuristic_reference"}
    assert bd["goal_alignment"] in {"high", "moderate", "low", "poor"}


def test_low_sodium_restriction_triggers_sodium_flag():
    """Usuario com restricao low_sodium deve receber aviso de sodio."""
    ind = pd.Series({
        "restriction_low_sodium": 1,
        "hypertension": "none",
        "glycemic_condition": "none",
        "total_cholesterol": 180,
        "goal": "maintenance",
        "diet_type": "omnivore",
    })
    food = pd.Series({
        "sodium_mg_100g": 450.0,
        "sugar_100g": 1.0,
        "saturated_fat_100g": 1.0,
        "proteins_100g": 5.0,
        "energy_kcal_100g": 100.0,
        "fiber_100g": 2.0,
        "food_group": "grain",
        "is_animal_product": 0, "is_meat": 0, "is_fish": 0,
    })
    for a in ["gluten", "lactose", "nuts", "shellfish", "eggs", "soy"]:
        ind[f"allergy_{a}"] = 0
        food[f"contains_{a}"] = 0

    breakdown = build_breakdown(ind, food, heuristic_score=6.0)
    assert any("sodium" in flag for flag in breakdown["health_flags"])
