from typing import Literal

from pydantic import BaseModel, Field

Goal = Literal["EMAGRECER", "GANHAR_MASSA", "MANTER"]
DietType = Literal["omnivore", "vegetarian", "vegan", "keto", "pescatarian", "paleo"]
ActivityLevel = Literal["sedentary", "lightly_active", "moderately_active", "very_active"]
Allergen = Literal["gluten", "lactose", "nuts", "shellfish", "eggs", "soy"]
Restriction = Literal["low_sodium", "low_sugar", "low_fat", "high_protein", "low_carb"]

PROFILE_EXAMPLE = {
    "age": 30, "height_cm": 170.0, "weight_kg": 80.0,
    "goal": "EMAGRECER", "diet_type": "vegetarian", "activity_level": "lightly_active",
    "cholesterol": 210, "glucose": 110,
    "restrictions": ["low_sugar"], "preferences": ["doces"], "allergies": ["lactose"],
}


class ProfileIn(BaseModel):
    age: int = Field(ge=18, le=110)
    height_cm: float = Field(gt=100, le=250)
    weight_kg: float = Field(gt=30, le=300)
    goal: Goal
    diet_type: DietType = "omnivore"
    activity_level: ActivityLevel = "lightly_active"
    cholesterol: int | None = Field(default=None, ge=100, le=400)
    glucose: int | None = Field(default=None, ge=40, le=500,
                                description="Glicemia de jejum em mg/dL")
    restrictions: list[Restriction] = []
    preferences: list[str] = []
    allergies: list[Allergen] = []

    model_config = {"json_schema_extra": {"examples": [PROFILE_EXAMPLE]}}


class ProfileOut(ProfileIn):
    user_id: str
