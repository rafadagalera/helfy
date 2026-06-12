import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core_api.auth.deps import get_current_user, require_owner
from core_api.db.models import Profile, User
from core_api.db.session import get_db
from core_api.recipes.service import suggest_recipes

router = APIRouter(prefix="/receitas", tags=["recipes"])


@router.get("/sugeridas/{usuario_id}",
            summary="Receitas viáveis com a dispensa atual, ranqueadas por score "
                    "(determinístico; 'scored'=false indica degradação sem engine)")
def suggested(usuario_id: uuid.UUID, limit: int = 10,
              user: User = Depends(get_current_user),
              db: Session = Depends(get_db)) -> dict:
    require_owner(user, usuario_id)
    profile = db.get(Profile, usuario_id)
    if profile is None:
        raise HTTPException(status_code=409,
                            detail="Cadastre o perfil antes de pedir sugestões")
    return suggest_recipes(db, profile, limit=limit)
