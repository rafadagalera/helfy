from pydantic import BaseModel, Field

NUTRITION_KEYS_DOC = ("energy_kcal_100g, proteins_100g, carbohydrates_100g, fat_100g, "
                      "saturated_fat_100g, fiber_100g, sodium_mg_100g, sugar_100g")


class FoodManualIn(BaseModel):
    """Input manual de produto (SCRUM-15)."""
    name: str = Field(min_length=1, max_length=255, description="Nome do alimento")
    food_group: str = Field(
        default="other",
        description="Grupo alimentar: grain, vegetable, fruit, meat, fish, "
                    "dairy, egg, legume, other")
    nutrition: dict[str, float] = Field(
        default_factory=dict,
        description=f"Info nutricional por 100g. Chaves canônicas: {NUTRITION_KEYS_DOC}")
    allergen_flags: list[str] = Field(
        default=[],
        description="Alérgenos presentes (gluten, lactose, nuts, shellfish, eggs, soy)")
    flags: list[str] = Field(
        default=[],
        description="Flags adicionais: animal_product, meat, fish")


class FoodOut(BaseModel):
    id: str = Field(description="UUID do alimento")
    barcode: str | None = Field(description="Código de barras EAN/UPC; null se não disponível")
    name: str = Field(description="Nome do alimento")
    food_group: str = Field(description="Grupo alimentar")
    nutrition: dict[str, float] = Field(
        description=f"Info nutricional por 100g. Chaves: {NUTRITION_KEYS_DOC}")
    allergen_flags: list[str] = Field(description="Alérgenos presentes neste alimento")
    flags: list[str] = Field(description="Flags adicionais do alimento")
    source: str = Field(description="Origem do cadastro: OFF (Open Food Facts), MANUAL, SEED")
