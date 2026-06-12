"""ScoreEngine: lote, escala 0–1, fallback heurístico explícito."""
from pathlib import Path

from score_engine.mapping.food import map_food
from score_engine.mapping.profile import map_profile
from score_engine.service import ScoreEngine
from tests.test_mapping import HELFY_FOOD, HELFY_PROFILE

ARTIFACTS = Path(__file__).parents[1] / "artifacts"


def test_scores_batch_in_unit_scale():
    engine = ScoreEngine(ARTIFACTS)
    assert engine.model_loaded

    profile_row = map_profile(HELFY_PROFILE)
    foods = [map_food(HELFY_FOOD), map_food({**HELFY_FOOD, "food_id": "xyz-789"})]

    results, engine_used = engine.score_pairs(profile_row, foods)

    assert engine_used == "mlp"
    assert [r["food_id"] for r in results] == ["abc-123", "xyz-789"]
    for r in results:
        assert 0.0 <= r["score"] <= 1.0
        assert "allergen_safe" in r["breakdown"]


def test_lactose_allergy_gives_zero_breakdown_unsafe():
    engine = ScoreEngine(ARTIFACTS)
    profile_row = map_profile({**HELFY_PROFILE, "allergies": ["lactose"]})
    results, _ = engine.score_pairs(profile_row, [map_food(HELFY_FOOD)])
    assert results[0]["breakdown"]["allergen_safe"] is False


def test_fallback_to_heuristic_when_artifacts_missing(tmp_path):
    engine = ScoreEngine(tmp_path)  # diretório sem .pkl
    assert not engine.model_loaded

    results, engine_used = engine.score_pairs(
        map_profile(HELFY_PROFILE), [map_food(HELFY_FOOD)]
    )
    assert engine_used == "heuristic"
    assert 0.0 <= results[0]["score"] <= 1.0
