"""Schemas do contrato público da engine — com exemplos para o OpenAPI (spec §7)."""
from typing import Literal

from pydantic import BaseModel, Field

PROFILE_EXAMPLE = {
    "goal": "EMAGRECER", "diet_type": "vegetarian", "activity_level": "lightly_active",
    "age": 30, "weight_kg": 80.0, "height_cm": 170.0,
    "total_cholesterol": 210, "glucose": 110,
    "allergies": ["lactose"], "restrictions": ["low_sugar"],
}

FOOD_EXAMPLE = {
    "food_id": "abc-123", "food_group": "dairy",
    "nutrition": {"energy_kcal_100g": 61.0, "proteins_100g": 3.3,
                  "carbohydrates_100g": 4.7, "fat_100g": 3.3,
                  "saturated_fat_100g": 1.9, "fiber_100g": 0.0,
                  "sodium_mg_100g": 40.0, "sugar_100g": 4.7},
    "allergen_flags": ["lactose"], "flags": ["animal_product"],
}


class ProfileIn(BaseModel):
    """Perfil de saúde no vocabulário do Helfy (a engine traduz para o modelo)."""
    goal: Literal["EMAGRECER", "GANHAR_MASSA", "MANTER"]
    diet_type: Literal["omnivore", "vegetarian", "vegan", "keto",
                       "pescatarian", "paleo"] = "omnivore"
    activity_level: Literal["sedentary", "lightly_active", "moderately_active",
                            "very_active"] = "lightly_active"
    age: int = Field(ge=18, le=110)
    weight_kg: float = Field(gt=30, le=300)
    height_cm: float = Field(gt=100, le=250)
    total_cholesterol: int | None = Field(default=None, ge=100, le=400)
    glucose: int | None = Field(default=None, ge=40, le=500,
                                description="Glicemia de jejum em mg/dL")
    allergies: list[Literal["gluten", "lactose", "nuts", "shellfish",
                            "eggs", "soy"]] = []
    restrictions: list[Literal["low_sodium", "low_sugar", "low_fat",
                               "high_protein", "low_carb"]] = []

    model_config = {"json_schema_extra": {"examples": [PROFILE_EXAMPLE]}}


class FoodIn(BaseModel):
    """Alimento com info nutricional por 100g, nas chaves canônicas da engine."""
    food_id: str
    food_group: str = "other"
    nutrition: dict[str, float] = Field(
        description="Chaves: energy_kcal_100g, proteins_100g, carbohydrates_100g, "
                    "fat_100g, saturated_fat_100g, fiber_100g, sodium_mg_100g, sugar_100g")
    allergen_flags: list[str] = []
    flags: list[Literal["animal_product", "meat", "fish"]] = []

    model_config = {"json_schema_extra": {"examples": [FOOD_EXAMPLE]}}


class ScoreRequest(BaseModel):
    profile: ProfileIn
    foods: list[FoodIn] = Field(min_length=1)


class Breakdown(BaseModel):
    allergen_safe: bool
    diet_compatible: bool
    goal_alignment: Literal["high", "moderate", "low", "poor"]
    health_flags: list[str]
    heuristic_reference: float = Field(description="Score da heurística na escala 0–10")


class ScoreItem(BaseModel):
    food_id: str
    score: float = Field(ge=0.0, le=1.0)
    breakdown: Breakdown


class ScoreResponse(BaseModel):
    scores: list[ScoreItem]
    model_version: str
    engine: Literal["mlp", "heuristic"] = Field(
        description="'heuristic' indica fallback por falha no carregamento do modelo")


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str
