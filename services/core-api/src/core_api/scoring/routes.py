from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core_api.auth.deps import get_current_user, require_owner
from core_api.db.models import Food, Profile, User
from core_api.db.session import get_db
from core_api.scoring.engine_client import EngineContractError, EngineUnavailableError
from core_api.scoring.schemas import ScoreOut, ScoreRequest
from core_api.scoring.service import get_scores, justification_from_breakdown

router = APIRouter(tags=["score"])


@router.post("/score", response_model=list[ScoreOut],
             summary="Score nutricional personalizado para um lote de alimentos")
def score(body: ScoreRequest, user: User = Depends(get_current_user),
          db: Session = Depends(get_db)) -> list[ScoreOut]:
    """Calcula o score de compatibilidade nutricional (0.0–1.0) de cada alimento
    para o perfil de saúde do usuário autenticado.

    Usa cache com TTL de 24h na tabela `food_scores`. O cache é invalidado
    automaticamente quando o perfil é atualizado via PUT /perfil/{usuario_id}.

    Retorna 409 se o perfil ainda não foi cadastrado.
    Retorna 503 se a engine de score estiver indisponível.
    """
    require_owner(user, body.usuario_id)
    profile = db.get(Profile, body.usuario_id)
    if profile is None:
        raise HTTPException(status_code=409,
                            detail="Cadastre o perfil antes de pedir scores personalizados")

    foods = [db.get(Food, fid) for fid in body.alimento_ids]
    missing_ids = [str(fid) for fid, f in zip(body.alimento_ids, foods) if f is None]
    if missing_ids:
        raise HTTPException(status_code=404,
                            detail=f"Alimentos não encontrados: {', '.join(missing_ids)}")

    try:
        scores = get_scores(db, profile, foods)
    except EngineUnavailableError:
        raise HTTPException(status_code=503, detail="Engine de score indisponível")
    except EngineContractError:
        raise HTTPException(status_code=500,
                            detail="Erro de contrato com a engine de score")

    return [ScoreOut(alimento_id=str(f.id), score=scores[str(f.id)]["score"],
                     justificativa=justification_from_breakdown(scores[str(f.id)]["breakdown"]))
            for f in foods]
