from core_api.db.models import Food

from tests.helpers import auth_headers


def _seed_food(db, name="Banana", barcode=None):
    food = Food(name=name, barcode=barcode, food_group="fruit",
                nutrition={"energy_kcal_100g": 89.0}, source="MANUAL")
    db.add(food)
    db.commit()
    return str(food.id)


def test_add_by_food_id_and_list(client, db):
    headers, user_id = auth_headers(client)
    food_id = _seed_food(db)

    resp = client.post(f"/dispensa/{user_id}/adicionar", headers=headers,
                       json={"alimento_id": food_id, "quantidade": 3})
    assert resp.status_code == 201

    resp = client.get(f"/dispensa/{user_id}", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["food"]["name"] == "Banana"
    assert items[0]["quantidade"] == 3


def test_add_by_barcode_uses_local_food(client, db):
    headers, user_id = auth_headers(client)
    _seed_food(db, name="Iogurte", barcode="789100")

    resp = client.post(f"/dispensa/{user_id}/adicionar", headers=headers,
                       json={"codigo_barras": "789100"})
    assert resp.status_code == 201
    items = client.get(f"/dispensa/{user_id}", headers=headers).json()
    assert items[0]["food"]["name"] == "Iogurte"


def test_add_same_food_twice_updates_quantity(client, db):
    headers, user_id = auth_headers(client)
    food_id = _seed_food(db)
    client.post(f"/dispensa/{user_id}/adicionar", headers=headers,
                json={"alimento_id": food_id, "quantidade": 1})
    client.post(f"/dispensa/{user_id}/adicionar", headers=headers,
                json={"alimento_id": food_id, "quantidade": 5})
    items = client.get(f"/dispensa/{user_id}", headers=headers).json()
    assert len(items) == 1
    assert items[0]["quantidade"] == 5


def test_remove_food(client, db):
    headers, user_id = auth_headers(client)
    food_id = _seed_food(db)
    client.post(f"/dispensa/{user_id}/adicionar", headers=headers,
                json={"alimento_id": food_id})
    resp = client.delete(f"/dispensa/{user_id}/{food_id}", headers=headers)
    assert resp.status_code == 204
    assert client.get(f"/dispensa/{user_id}", headers=headers).json() == []


def test_other_users_pantry_403(client, db):
    headers_a, _ = auth_headers(client, email="a@helfy.app")
    _, user_b = auth_headers(client, email="b@helfy.app")
    assert client.get(f"/dispensa/{user_b}", headers=headers_a).status_code == 403
