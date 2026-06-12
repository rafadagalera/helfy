import respx
from httpx import Response

from core_api.db.models import Food
from core_api.seed import run_seed
from core_api.settings import settings

from tests.helpers import auth_headers
from tests.test_profile import PROFILE

ENGINE_URL = f"{settings.score_engine_url}/score"


def _engine_ok(request):
    """Mock dinâmico: score 0.9 para qualquer alimento pedido."""
    import json
    payload = json.loads(request.content)
    scores = [{"food_id": f["food_id"], "score": 0.9,
               "breakdown": {"allergen_safe": True, "diet_compatible": True,
                             "goal_alignment": "high", "health_flags": [],
                             "heuristic_reference": 9.0}}
              for f in payload["foods"]]
    return Response(200, json={"scores": scores, "model_version": "mlp-v1", "engine": "mlp"})


def _setup(client, db):
    run_seed(db)
    headers, user_id = auth_headers(client)
    client.put(f"/perfil/{user_id}", json=PROFILE, headers=headers)

    # Dispensa: banana + aveia + iogurte → cobre 100% de "Vitamina de banana com aveia"
    # e 100% de "Mingau de aveia com banana"
    for name in ["Banana", "Aveia em flocos", "Iogurte natural"]:
        food = db.query(Food).filter_by(name=name).one()
        client.post(f"/dispensa/{user_id}/adicionar", headers=headers,
                    json={"alimento_id": str(food.id)})
    return headers, user_id


@respx.mock
def test_suggestions_only_include_covered_recipes(client, db):
    respx.post(ENGINE_URL).mock(side_effect=_engine_ok)
    headers, user_id = _setup(client, db)

    resp = client.get(f"/receitas/sugeridas/{user_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["scored"] is True
    names = [r["name"] for r in body["receitas"]]
    assert "Vitamina de banana com aveia" in names
    assert "Mingau de aveia com banana" in names
    assert "Tilápia com legumes" not in names  # cobertura 0%
    for r in body["receitas"]:
        assert r["coverage"] >= 0.7


@respx.mock
def test_suggestions_are_deterministic(client, db):
    respx.post(ENGINE_URL).mock(side_effect=_engine_ok)
    headers, user_id = _setup(client, db)
    first = client.get(f"/receitas/sugeridas/{user_id}", headers=headers).json()
    second = client.get(f"/receitas/sugeridas/{user_id}", headers=headers).json()
    assert first == second


@respx.mock
def test_engine_down_degrades_to_coverage_order(client, db):
    respx.post(ENGINE_URL).mock(side_effect=Exception("down"))
    headers, user_id = _setup(client, db)

    resp = client.get(f"/receitas/sugeridas/{user_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["scored"] is False
    assert all(r["score_medio"] is None for r in body["receitas"])
    assert len(body["receitas"]) >= 1

    # Verify ordering: coverage desc, then name asc for ties
    coverages = [r["coverage"] for r in body["receitas"]]
    assert coverages == sorted(coverages, reverse=True)
    # At equal coverage, names must be alphabetically sorted
    equal_groups = {}
    for r in body["receitas"]:
        equal_groups.setdefault(r["coverage"], []).append(r["name"])
    for cov, names in equal_groups.items():
        assert names == sorted(names), f"coverage={cov}: names not sorted: {names}"


def test_empty_pantry_returns_empty_list(client, db):
    run_seed(db)
    headers, user_id = auth_headers(client)
    client.put(f"/perfil/{user_id}", json=PROFILE, headers=headers)
    body = client.get(f"/receitas/sugeridas/{user_id}", headers=headers).json()
    assert body["receitas"] == []
