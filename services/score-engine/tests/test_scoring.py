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


def test_breakdown_structure():
    bd = build_breakdown(_ind(allergy_nuts=1), _food(contains_nuts=1), heuristic_score=0.0)
    assert bd["allergen_safe"] is False
    assert set(bd) == {"allergen_safe", "diet_compatible", "goal_alignment",
                       "health_flags", "heuristic_reference"}
    assert bd["goal_alignment"] in {"high", "moderate", "low", "poor"}
