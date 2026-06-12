import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core_api.auth.deps import get_current_user, require_owner
from core_api.db.models import Food, Profile, User
from core_api.db.session import get_db
from core_api.scoring.engine_client import EngineUnavailableError
from core_api.scoring.service import get_scores, justification_from_breakdown

router = APIRouter(tags=["score"])


class ScoreRequest(BaseModel):
    usuario_id: uuid.UUID
    alimento_ids: list[uuid.UUID] = Field(min_length=1)


class ScoreOut(BaseModel):
    alimento_id: str
    score: float = Field(ge=0.0, le=1.0)
    justificativa: str


@router.post("/score", response_model=list[ScoreOut],
             summary="Score nutricional personalizado para um lote de alimentos")
def score(body: ScoreRequest, user: User = Depends(get_current_user),
          db: Session = Depends(get_db)) -> list[ScoreOut]:
    require_owner(user, body.usuario_id)
    profile = db.get(Profile, body.usuario_id)
    if profile is None:
        raise HTTPException(status_code=409,
                            detail="Cadastre o perfil antes de pedir scores personalizados")

    foods = [db.get(Food, fid) for fid in body.alimento_ids]
    if any(f is None for f in foods):
        raise HTTPException(status_code=404, detail="Alimento não encontrado")

    try:
        scores = get_scores(db, profile, foods)
    except EngineUnavailableError:
        raise HTTPException(status_code=503, detail="Engine de score indisponível")

    return [ScoreOut(alimento_id=str(f.id), score=scores[str(f.id)]["score"],
                     justificativa=justification_from_breakdown(scores[str(f.id)]["breakdown"]))
            for f in foods]
