import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core_api.auth.security import decode_token
from core_api.db.models import User
from core_api.db.session import get_db

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Token ausente")
    user_id = decode_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    user = db.get(User, uuid.UUID(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="Usuário não existe")
    return user


def require_owner(user: User, usuario_id: uuid.UUID) -> None:
    """Garante que o usuário autenticado só acessa os próprios recursos."""
    if user.id != usuario_id:
        raise HTTPException(status_code=403, detail="Acesso negado a recurso de outro usuário")
