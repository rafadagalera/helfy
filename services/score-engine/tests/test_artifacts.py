"""Sanidade: artefatos replicados carregam e produzem predição plausível."""
from pathlib import Path

import joblib
import pandas as pd

from score_engine.features.preprocessing import ALL_FEATURE_COLS

ARTIFACTS = Path(__file__).parents[1] / "artifacts"

# Linha bruta válida: omnívoro saudável × fruta — par sabidamente bem avaliado
SAMPLE_ROW = {
    "age": 35, "total_cholesterol": 180, "weight_kg": 70.0, "height_cm": 175.0, "bmi": 22.9,
    "diet_type": "omnivore", "goal": "maintenance", "activity_level": "moderately_active",
    "glycemic_condition": "none", "hypertension": "none",
    "allergy_gluten": 0, "allergy_lactose": 0, "allergy_nuts": 0,
    "allergy_shellfish": 0, "allergy_eggs": 0, "allergy_soy": 0,
    "restriction_low_sodium": 0, "restriction_low_sugar": 0, "restriction_low_fat": 0,
    "restriction_high_protein": 0, "restriction_low_carb": 0,
    "energy_kcal_100g": 52.0, "proteins_100g": 0.3, "carbohydrates_100g": 14.0,
    "fat_100g": 0.2, "saturated_fat_100g": 0.0, "fiber_100g": 2.4,
    "sodium_mg_100g": 1.0, "sugar_100g": 10.0,
    "food_group": "fruit",
    "contains_gluten": 0, "contains_lactose": 0, "contains_nuts": 0,
    "contains_shellfish": 0, "contains_eggs": 0, "contains_soy": 0,
    "is_animal_product": 0, "is_meat": 0, "is_fish": 0,
}


def test_artifacts_load_and_predict():
    model = joblib.load(ARTIFACTS / "mlp_model.pkl")
    preprocessor = joblib.load(ARTIFACTS / "preprocessor.pkl")

    df = pd.DataFrame([SAMPLE_ROW]).reindex(columns=ALL_FEATURE_COLS, fill_value=0)
    X = preprocessor.transform(df)
    pred = float(model.predict(X)[0])

    assert 0.0 <= pred <= 10.5  # saída bruta do MLP, antes do clip
    assert pred >= 5.0  # fruta para omnívoro saudável: score alto


def test_feature_columns_unchanged():
    # O contrato do preprocessador depende destas 39 colunas — mudou, quebrou o modelo
    assert len(ALL_FEATURE_COLS) == 39
