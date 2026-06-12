"""
Helfy Score Engine — API stateless de score nutricional.

Recebe perfil Helfy + alimentos no request; não persiste nada (spec §2).
Swagger UI em /docs, ReDoc em /redoc (spec §7).
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from score_engine.api.schemas import (
    HealthResponse,
    ScoreRequest,
    ScoreResponse,
)
from score_engine.mapping.food import map_food
from score_engine.mapping.profile import map_profile
from score_engine.service import MODEL_VERSION, ScoreEngine

logging.basicConfig(level=logging.INFO,
                    format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')

# api/ → score_engine → src → score-engine (raiz do serviço)
ARTIFACTS_DIR = Path(__file__).parents[3] / "artifacts"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = ScoreEngine(ARTIFACTS_DIR)
    yield


app = FastAPI(
    title="Helfy Score Engine",
    description="Score de compatibilidade nutricional (0.0–1.0) por par usuário × alimento. "
                "Serviço stateless: o perfil e os alimentos chegam no corpo da requisição.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["system"],
         summary="Status do serviço e do modelo")
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=app.state.engine.model_loaded,
        model_version=MODEL_VERSION,
    )


@app.post("/score", response_model=ScoreResponse, tags=["score"],
          summary="Pontua um lote de alimentos para um perfil")
def score(body: ScoreRequest) -> ScoreResponse:
    profile_row = map_profile(body.profile.model_dump())
    food_rows = [map_food(food.model_dump()) for food in body.foods]
    results, engine_used = app.state.engine.score_pairs(profile_row, food_rows)
    return ScoreResponse(scores=results, model_version=MODEL_VERSION, engine=engine_used)
