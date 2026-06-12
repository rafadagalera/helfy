import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core_api.auth.deps import get_current_user, require_owner
from core_api.db.models import Profile, User
from core_api.db.session import get_db
from core_api.recipes.schemas import RecipeSuggestionResponse
from core_api.recipes.service import suggest_recipes

router = APIRouter(prefix="/receitas", tags=["recipes"])


@router.get(
    "/sugeridas/{usuario_id}",
    response_model=RecipeSuggestionResponse,
    summary="Receitas viáveis com a dispensa atual, ranqueadas por score",
)
def suggested(
    usuario_id: uuid.UUID,
    limit: int = Query(default=10, ge=1, le=50,
                       description="Número máximo de receitas retornadas"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecipeSuggestionResponse:
    """Sugere receitas pré-cadastradas que o usuário consegue preparar com sua dispensa atual.

    Critério de elegibilidade: cobertura de ingredientes ≥ 70%.
    Ordenação: score médio dos ingredientes disponíveis (desc), cobertura (desc), nome (asc).
    Se a engine de score estiver indisponível, degrada para ordenação por cobertura
    e retorna `scored: false`.

    Requer perfil cadastrado. Retorna 409 se o perfil não existir.
    """
    require_owner(user, usuario_id)
    profile = db.get(Profile, usuario_id)
    if profile is None:
        raise HTTPException(status_code=409,
                            detail="Cadastre o perfil antes de pedir sugestões")
    return suggest_recipes(db, profile, limit=limit)
