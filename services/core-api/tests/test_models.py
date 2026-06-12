import uuid

from core_api.db.models import Food, PantryItem, Profile, Recipe, RecipeIngredient, User


def test_full_schema_roundtrip(db):
    user = User(email="a@b.com", password_hash="x", name="Ana")
    db.add(user)
    db.flush()

    db.add(Profile(user_id=user.id, age=30, height_cm=170.0, weight_kg=80.0,
                   goal="EMAGRECER", diet_type="vegetarian",
                   restrictions=["low_sugar"], allergies=["lactose"], preferences=[]))

    food = Food(name="Iogurte natural", barcode="789100", food_group="dairy",
                nutrition={"energy_kcal_100g": 61.0}, allergen_flags=["lactose"],
                flags=["animal_product"], source="OFF")
    db.add(food)
    db.flush()

    db.add(PantryItem(user_id=user.id, food_id=food.id))
    recipe = Recipe(name="Iogurte com frutas", instructions="Misture tudo.",
                    nutrition_total={})
    db.add(recipe)
    db.flush()
    db.add(RecipeIngredient(recipe_id=recipe.id, food_id=food.id, quantity="1 pote"))
    db.commit()

    loaded = db.get(User, user.id)
    assert loaded.profile.goal == "EMAGRECER"
    assert isinstance(loaded.id, uuid.UUID)
