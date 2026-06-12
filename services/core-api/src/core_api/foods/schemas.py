from pydantic import BaseModel, Field

NUTRITION_KEYS_DOC = ("energy_kcal_100g, proteins_100g, carbohydrates_100g, fat_100g, "
                      "saturated_fat_100g, fiber_100g, sodium_mg_100g, sugar_100g")


class FoodManualIn(BaseModel):
    """Input manual de produto (SCRUM-15)."""
    name: str = Field(min_length=1, max_length=255)
    food_group: str = "other"
    nutrition: dict[str, float] = Field(default_factory=dict,
                                        description=f"Por 100g. Chaves: {NUTRITION_KEYS_DOC}")
    allergen_flags: list[str] = []
    flags: list[str] = []


class FoodOut(BaseModel):
    id: str
    barcode: str | None
    name: str
    food_group: str
    nutrition: dict[str, float]
    allergen_flags: list[str]
    flags: list[str]
    source: str
