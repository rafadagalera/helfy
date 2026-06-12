from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from core_api.auth.deps import get_current_user
from core_api.auth.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from core_api.auth.security import create_access_token, hash_password, verify_password
from core_api.db.models import User
from core_api.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201,
             summary="Cria um usuário")
def register(body: RegisterIn, db: Session = Depends(get_db)) -> UserOut:
    exists = db.scalar(select(User).where(User.email == body.email))
    if exists:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    user = User(email=body.email, password_hash=hash_password(body.password), name=body.name)
    db.add(user)
    db.commit()
    return UserOut(id=str(user.id), email=user.email, name=user.name)


@router.post("/login", response_model=TokenOut, summary="Autentica e retorna JWT")
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut, summary="Usuário autenticado")
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=str(user.id), email=user.email, name=user.name)
