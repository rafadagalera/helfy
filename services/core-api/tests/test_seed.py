from core_api.db.models import Food, Recipe
from core_api.seed import run_seed


def test_seed_is_idempotent(db):
    run_seed(db)
    foods_count = db.query(Food).count()
    recipes_count = db.query(Recipe).count()
    assert foods_count == 20
    assert recipes_count == 20

    run_seed(db)  # segunda execução não duplica
    assert db.query(Food).count() == foods_count
    assert db.query(Recipe).count() == recipes_count


def test_seeded_recipe_has_ingredients(db):
    run_seed(db)
    recipe = db.query(Recipe).filter_by(name="Arroz com feijão e frango grelhado").one()
    assert len(recipe.ingredients) == 3
