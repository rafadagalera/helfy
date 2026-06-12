"""Tradução perfil Helfy → features do modelo, e alimento Helfy → features."""
import pytest

from score_engine.features.preprocessing import ALL_FEATURE_COLS
from score_engine.mapping.food import map_food
from score_engine.mapping.profile import map_profile

HELFY_PROFILE = {
    "goal": "EMAGRECER", "diet_type": "vegetarian", "activity_level": "lightly_active",
    "age": 30, "weight_kg": 80.0, "height_cm": 170.0,
    "total_cholesterol": 210, "glucose": 110,
    "allergies": ["lactose"], "restrictions": ["low_sugar"],
}

HELFY_FOOD = {
    "food_id": "abc-123", "food_group": "dairy",
    "nutrition": {"energy_kcal_100g": 61.0, "proteins_100g": 3.3,
                  "carbohydrates_100g": 4.7, "fat_100g": 3.3,
                  "saturated_fat_100g": 1.9, "fiber_100g": 0.0,
                  "sodium_mg_100g": 40.0, "sugar_100g": 4.7},
    "allergen_flags": ["lactose"], "flags": ["animal_product"],
}


def test_goal_is_translated():
    assert map_profile(HELFY_PROFILE)["goal"] == "weight_loss"
    assert map_profile({**HELFY_PROFILE, "goal": "GANHAR_MASSA"})["goal"] == "muscle_gain"
    assert map_profile({**HELFY_PROFILE, "goal": "MANTER"})["goal"] == "maintenance"


@pytest.mark.parametrize("glucose,expected", [
    (None, "none"), (90, "none"), (100, "pre_diabetic"),
    (125, "pre_diabetic"), (126, "type_2"), (200, "type_2"),
])
def test_glucose_maps_to_glycemic_condition(glucose, expected):
    row = map_profile({**HELFY_PROFILE, "glucose": glucose})
    assert row["glycemic_condition"] == expected


def test_bmi_is_computed():
    assert map_profile(HELFY_PROFILE)["bmi"] == pytest.approx(27.7, abs=0.05)


def test_allergies_and_restrictions_become_flags():
    row = map_profile(HELFY_PROFILE)
    assert row["allergy_lactose"] == 1
    assert row["allergy_gluten"] == 0
    assert row["restriction_low_sugar"] == 1
    assert row["restriction_low_carb"] == 0


def test_defaults_for_missing_health_data():
    row = map_profile({**HELFY_PROFILE, "total_cholesterol": None, "glucose": None})
    assert row["total_cholesterol"] == 180  # mediana populacional como default
    assert row["glycemic_condition"] == "none"
    assert row["hypertension"] == "none"  # Sprint 1 não coleta pressão arterial


def test_food_mapping_produces_model_columns():
    row = map_food(HELFY_FOOD)
    assert row["food_id"] == "abc-123"
    assert row["energy_kcal_100g"] == 61.0
    assert row["contains_lactose"] == 1
    assert row["contains_gluten"] == 0
    assert row["is_animal_product"] == 1
    assert row["is_meat"] == 0


def test_profile_plus_food_covers_all_model_columns():
    merged = {**map_profile(HELFY_PROFILE), **map_food(HELFY_FOOD)}
    missing = [c for c in ALL_FEATURE_COLS if c not in merged]
    assert missing == []
