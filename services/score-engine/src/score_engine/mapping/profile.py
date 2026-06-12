"""
Traduz o perfil Helfy (domínio do produto) para a linha de features do modelo.

Defaults documentados (spec §4.2):
- total_cholesterol ausente → 180 (mediana populacional)
- glucose ausente → glycemic_condition "none"
- hypertension → sempre "none" (o perfil da Sprint 1 não coleta pressão arterial)
"""
GOAL_MAP = {
    "EMAGRECER": "weight_loss",
    "GANHAR_MASSA": "muscle_gain",
    "MANTER": "maintenance",
}

VALID_ALLERGENS = ["gluten", "lactose", "nuts", "shellfish", "eggs", "soy"]
VALID_RESTRICTIONS = ["low_sodium", "low_sugar", "low_fat", "high_protein", "low_carb"]

DEFAULT_CHOLESTEROL = 180


def glycemic_condition_from_glucose(glucose: int | None) -> str:
    """Faixas clínicas de glicemia de jejum (mg/dL)."""
    if glucose is None or glucose < 100:
        return "none"
    if glucose < 126:
        return "pre_diabetic"
    return "type_2"


def map_profile(profile: dict) -> dict:
    height_m = profile["height_cm"] / 100
    bmi = round(profile["weight_kg"] / height_m**2, 1)

    row = {
        "age": profile["age"],
        "total_cholesterol": profile.get("total_cholesterol") or DEFAULT_CHOLESTEROL,
        "weight_kg": profile["weight_kg"],
        "height_cm": profile["height_cm"],
        "bmi": bmi,
        "diet_type": profile.get("diet_type") or "omnivore",
        "goal": GOAL_MAP[profile["goal"]],
        "activity_level": profile.get("activity_level") or "lightly_active",
        "glycemic_condition": glycemic_condition_from_glucose(profile.get("glucose")),
        "hypertension": "none",
    }

    allergies = set(profile.get("allergies") or [])
    restrictions = set(profile.get("restrictions") or [])
    for allergen in VALID_ALLERGENS:
        row[f"allergy_{allergen}"] = int(allergen in allergies)
    for restriction in VALID_RESTRICTIONS:
        row[f"restriction_{restriction}"] = int(restriction in restrictions)
    return row
