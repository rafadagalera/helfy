import respx
from httpx import Response

from core_api.foods.off_client import normalize_off_product
from core_api.settings import settings

from tests.helpers import auth_headers

OFF_PRODUCT = {
    "status": 1,
    "product": {
        "product_name": "Iogurte Natural Integral",
        "categories_tags": ["en:dairies", "en:yogurts"],
        "allergens_tags": ["en:milk"],
        "nutriments": {
            "energy-kcal_100g": 61.0, "proteins_100g": 3.3, "carbohydrates_100g": 4.7,
            "fat_100g": 3.3, "saturated-fat_100g": 1.9, "fiber_100g": 0.0,
            "sodium_100g": 0.04, "sugars_100g": 4.7,
        },
    },
}


def test_normalize_off_product_maps_fields():
    food = normalize_off_product("7891000100103", OFF_PRODUCT["product"])
    assert food["name"] == "Iogurte Natural Integral"
    assert food["food_group"] == "dairy"
    assert food["allergen_flags"] == ["lactose"]
    assert food["flags"] == ["animal_product"]
    assert food["nutrition"]["sodium_mg_100g"] == 40.0  # OFF dá sódio em g → mg
    assert food["nutrition"]["sugar_100g"] == 4.7       # sugars_100g → sugar_100g


@respx.mock
def test_barcode_miss_fetches_from_off_and_persists(client):
    headers, _ = auth_headers(client)
    respx.get(f"{settings.off_base_url}/api/v2/product/7891000100103.json").mock(
        return_value=Response(200, json=OFF_PRODUCT))

    resp = client.get("/alimentos/barcode/7891000100103", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["source"] == "OFF"

    # Segunda chamada: cache local, sem novo hit no OFF
    respx.calls.assert_called_once()
    resp2 = client.get("/alimentos/barcode/7891000100103", headers=headers)
    assert resp2.status_code == 200
    assert respx.calls.call_count == 1


@respx.mock
def test_barcode_not_found_in_off_404(client):
    headers, _ = auth_headers(client)
    respx.get(f"{settings.off_base_url}/api/v2/product/000.json").mock(
        return_value=Response(200, json={"status": 0}))
    assert client.get("/alimentos/barcode/000", headers=headers).status_code == 404


@respx.mock
def test_off_unavailable_502(client):
    headers, _ = auth_headers(client)
    respx.get(f"{settings.off_base_url}/api/v2/product/111.json").mock(
        side_effect=Exception("timeout"))
    assert client.get("/alimentos/barcode/111", headers=headers).status_code == 502


def test_manual_food_creation_and_get(client):
    headers, _ = auth_headers(client)
    resp = client.post("/alimentos", headers=headers, json={
        "name": "Arroz integral caseiro", "food_group": "grain",
        "nutrition": {"energy_kcal_100g": 124.0, "proteins_100g": 2.6,
                      "carbohydrates_100g": 25.8, "fat_100g": 1.0,
                      "saturated_fat_100g": 0.3, "fiber_100g": 2.7,
                      "sodium_mg_100g": 1.0, "sugar_100g": 0.4},
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["source"] == "MANUAL"

    resp = client.get(f"/alimentos/{body['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Arroz integral caseiro"
