import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlalchemy.orm import Session

from core_api.auth.deps import get_current_user, require_owner
from core_api.db.models import FoodScore, Profile, User
from core_api.db.session import get_db
from core_api.profile.schemas import ProfileIn, ProfileOut

router = APIRouter(prefix="/perfil", tags=["profile"])


def _to_out(profile: Profile) -> ProfileOut:
    return ProfileOut(user_id=str(profile.user_id), age=profile.age,
                      height_cm=profile.height_cm, weight_kg=profile.weight_kg,
                      goal=profile.goal, diet_type=profile.diet_type,
                      activity_level=profile.activity_level,
                      cholesterol=profile.cholesterol, glucose=profile.glucose,
                      restrictions=profile.restrictions, preferences=profile.preferences,
                      allergies=profile.allergies)


@router.get("/{usuario_id}", response_model=ProfileOut, summary="Retorna o perfil")
def get_profile(usuario_id: uuid.UUID, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)) -> ProfileOut:
    require_owner(user, usuario_id)
    profile = db.get(Profile, usuario_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil ainda não cadastrado")
    return _to_out(profile)


@router.put("/{usuario_id}", response_model=ProfileOut,
            summary="Cria/atualiza o perfil (invalida o cache de scores)")
def put_profile(usuario_id: uuid.UUID, body: ProfileIn,
                user: User = Depends(get_current_user),
                db: Session = Depends(get_db)) -> ProfileOut:
    require_owner(user, usuario_id)
    profile = db.get(Profile, usuario_id)
    if profile is None:
        profile = Profile(user_id=usuario_id)
        db.add(profile)
    for field, value in body.model_dump().items():
        setattr(profile, field, value)

    # Perfil mudou → scores personalizados ficam obsoletos (spec §5)
    db.execute(delete(FoodScore).where(FoodScore.user_id == usuario_id))
    db.commit()
    return _to_out(profile)
