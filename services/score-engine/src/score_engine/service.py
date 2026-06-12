"""
Núcleo do serviço: carrega artefatos e pontua pares perfil × alimentos em lote.

O modelo prevê na escala 0–10 (escala de treino); a borda pública do Helfy
usa 0.0–1.0, então a normalização (÷10) acontece aqui, uma única vez.
"""
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from score_engine.features.preprocessing import ALL_FEATURE_COLS
from score_engine.scoring import build_breakdown, compute_score

logger = logging.getLogger(__name__)

MODEL_VERSION = "mlp-v1"


class ScoreEngine:
    def __init__(self, artifacts_dir: Path):
        self.model = None
        self.preprocessor = None
        try:
            self.model = joblib.load(artifacts_dir / "mlp_model.pkl")
            self.preprocessor = joblib.load(artifacts_dir / "preprocessor.pkl")
            logger.info("artefatos carregados de %s", artifacts_dir)
        except FileNotFoundError as exc:
            logger.warning("artefatos ausentes (%s) — operando em modo heurístico", exc)

    @property
    def model_loaded(self) -> bool:
        return self.model is not None and self.preprocessor is not None

    def score_pairs(
        self, profile_row: dict, food_rows: list[dict]
    ) -> tuple[list[dict], str]:
        """Retorna ([{food_id, score 0–1, breakdown}], "mlp" | "heuristic")."""
        ind = pd.Series(profile_row)

        if self.model_loaded:
            df = pd.DataFrame([{**profile_row, **food} for food in food_rows])
            df = df.reindex(columns=ALL_FEATURE_COLS, fill_value=0)
            X = self.preprocessor.transform(df)
            raw_scores = np.clip(self.model.predict(X), 0.0, 10.0)
            engine_used = "mlp"
        else:
            raw_scores = [
                compute_score(ind, pd.Series(food), noise_std=0.0) for food in food_rows
            ]
            engine_used = "heuristic"

        results = []
        for food_row, raw in zip(food_rows, raw_scores):
            food = pd.Series(food_row)
            heuristic = compute_score(ind, food, noise_std=0.0)
            results.append({
                "food_id": food_row["food_id"],
                "score": round(float(raw) / 10.0, 3),
                "breakdown": build_breakdown(ind, food, heuristic),
            })
        return results, engine_used
