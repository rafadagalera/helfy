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
    goal: Literal["EMAGRECER", "GANHAR_MASSA", "MANTER"] = Field(
        description="Objetivo de saúde: EMAGRECER (perda de peso), "
                    "GANHAR_MASSA (hipertrofia) ou MANTER (manutenção)")
    diet_type: Literal["omnivore", "vegetarian", "vegan", "keto",
                       "pescatarian", "paleo"] = Field(
        default="omnivore",
        description="Tipo de dieta. Influencia a compatibilidade com alimentos de origem animal")
    activity_level: Literal["sedentary", "lightly_active", "moderately_active",
                            "very_active"] = Field(
        default="lightly_active",
        description="Nível de atividade física semanal")
    age: int = Field(ge=18, le=110, description="Idade em anos completos")
    weight_kg: float = Field(gt=30, le=300, description="Peso em quilogramas")
    height_cm: float = Field(gt=100, le=250, description="Altura em centímetros")
    total_cholesterol: int | None = Field(
        default=None, ge=100, le=400,
        description="Colesterol total em mg/dL. Omitir se não disponível — "
                    "o modelo usa 180 (mediana populacional) como default")
    glucose: int | None = Field(
        default=None, ge=40, le=500,
        description="Glicemia de jejum em mg/dL. Omitir se não disponível")
    allergies: list[Literal["gluten", "lactose", "nuts", "shellfish",
                            "eggs", "soy"]] = Field(
        default=[],
        description="Alérgenos aos quais o usuário é sensível")
    restrictions: list[Literal["low_sodium", "low_sugar", "low_fat",
                               "high_protein", "low_carb"]] = Field(
        default=[],
        description="Restrições nutricionais do usuário")

    model_config = {"json_schema_extra": {"examples": [PROFILE_EXAMPLE]}}


class FoodIn(BaseModel):
    """Alimento com info nutricional por 100g, nas chaves canônicas da engine."""
    food_id: str = Field(description="UUID do alimento no sistema Helfy")
    food_group: str = Field(
        default="other",
        description="Grupo alimentar: grain, vegetable, fruit, meat, fish, "
                    "dairy, egg, legume, other")
    nutrition: dict[str, float] = Field(
        description="Info nutricional por 100g. Chaves canônicas: energy_kcal_100g, "
                    "proteins_100g, carbohydrates_100g, fat_100g, saturated_fat_100g, "
                    "fiber_100g, sodium_mg_100g, sugar_100g")
    allergen_flags: list[str] = Field(
        default=[],
        description="Alérgenos presentes neste alimento "
                    "(gluten, lactose, nuts, shellfish, eggs, soy)")
    flags: list[Literal["animal_product", "meat", "fish"]] = Field(
        default=[],
        description="Flags adicionais: animal_product (qualquer produto animal), "
                    "meat (carne), fish (peixe/frutos do mar)")

    model_config = {"json_schema_extra": {"examples": [FOOD_EXAMPLE]}}


class ScoreRequest(BaseModel):
    profile: ProfileIn = Field(description="Perfil de saúde do usuário")
    foods: list[FoodIn] = Field(min_length=1, description="Lote de alimentos a pontuar (mínimo 1)")


class Breakdown(BaseModel):
    allergen_safe: bool = Field(
        description="True se o alimento não contém nenhum alérgeno presente no perfil")
    diet_compatible: bool = Field(
        description="True se o alimento é compatível com o tipo de dieta do usuário")
    goal_alignment: Literal["high", "moderate", "low", "poor"] = Field(
        description="Alinhamento do alimento com o objetivo de saúde: "
                    "high (forte), moderate, low ou poor (fraco)")
    health_flags: list[str] = Field(
        description="Alertas nutricionais quando sódio, açúcar ou gordura saturada "
                    "excedem os limites para o perfil (ex: hipertensão, diabetes)")
    heuristic_reference: float = Field(
        description="Score da heurística de referência na escala 0–10 "
                    "(o modelo MLP aprende a replicar este valor)")


class ScoreItem(BaseModel):
    food_id: str = Field(description="UUID do alimento, idêntico ao food_id enviado no request")
    score: float = Field(
        ge=0.0, le=1.0,
        description="Score de compatibilidade nutricional normalizado "
                    "(0.0 = incompatível, 1.0 = ideal para este perfil)")
    breakdown: Breakdown = Field(
        description="Componentes individuais que compõem e explicam o score")


class ScoreResponse(BaseModel):
    scores: list[ScoreItem] = Field(
        description="Score de cada alimento enviado, na mesma ordem do request")
    model_version: str = Field(description="Versão do modelo de score em uso")
    engine: Literal["mlp", "heuristic"] = Field(
        description="Motor utilizado: 'mlp' (modelo treinado) ou "
                    "'heuristic' (fallback quando o modelo não carregou)")


class HealthResponse(BaseModel):
    status: str = Field(description="Sempre 'ok' quando o serviço está respondendo")
    model_loaded: bool = Field(
        description="True se o modelo MLP foi carregado dos artefatos com sucesso; "
                    "False indica modo fallback heurístico")
    model_version: str = Field(description="Versão do modelo configurada no serviço")
