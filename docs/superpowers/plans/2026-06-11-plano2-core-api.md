# Plano 2 — core-api (auth, perfil, alimentos, dispensa, score, receitas)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar a `core-api` completa: autenticação JWT, perfil de saúde, base de alimentos (Open Food Facts + input manual), dispensa digital, endpoint público de score (com cache TTL 24h consumindo a score-engine) e sugestão determinística de receitas.

**Architecture:** Serviço FastAPI único, modularizado por domínio (`auth`, `profile`, `foods`, `pantry`, `scoring`, `recipes`), com PostgreSQL via SQLAlchemy 2 (sync) + Alembic. A score-engine (Plano 1) é consumida via HTTP pelo módulo `scoring`, que mantém o cache `food_scores` (TTL 24h + invalidação no update de perfil). Rotas públicas em português, conforme CLAUDE.md §6; código em inglês.

**Tech Stack:** Python 3.12, uv, FastAPI, Pydantic v2 + pydantic-settings, SQLAlchemy 2 (sync, psycopg), Alembic, python-jose + passlib[bcrypt], httpx (+ respx nos testes), pytest, ruff, Docker, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-06-11-helfy-monorepo-design.md` (seções 2, 5, 7–9)
**Pré-requisito:** Plano 1 executado (engine em `services/score-engine`, docker-compose com postgres na raiz).

**Convenções:** código em inglês; commits em português; NUNCA incluir trailers de IA nos commits. Rodar comandos via `uv run ...` dentro de `services/core-api/`.

---

## Contexto para quem nunca viu o projeto

- O contrato da **score-engine** (Plano 1): `POST {SCORE_ENGINE_URL}/score` com `{ "profile": {goal: "EMAGRECER|GANHAR_MASSA|MANTER", diet_type, activity_level, age, weight_kg, height_cm, total_cholesterol?, glucose?, allergies[], restrictions[]}, "foods": [{food_id, food_group, nutrition{energy_kcal_100g,...}, allergen_flags[], flags[]}] }` → `{ "scores": [{food_id, score: 0–1, breakdown{allergen_safe, diet_compatible, goal_alignment, health_flags[], heuristic_reference}}], "model_version", "engine": "mlp"|"heuristic" }`.
- Chaves canônicas de `nutrition` (por 100g): `energy_kcal_100g, proteins_100g, carbohydrates_100g, fat_100g, saturated_fat_100g, fiber_100g, sodium_mg_100g, sugar_100g`.
- Alérgenos válidos: `gluten, lactose, nuts, shellfish, eggs, soy`. Restrições válidas: `low_sodium, low_sugar, low_fat, high_protein, low_carb`. Flags de alimento: `animal_product, meat, fish`.
- Os testes usam um banco Postgres real (`helfy_test`) — suba antes com `docker compose up -d postgres`.

**Desvio registrado da spec §5:** a tabela `foods` ganha a coluna `flags text[]` (animal_product/meat/fish), ausente no schema da spec mas exigida pelo contrato da engine (dieta vegana/vegetariana). A spec menciona esses flags no contrato §4; a coluna é a forma de persisti-los.

---

### Task 1: Pacote core-api, settings e /health

**Files:**
- Create: `services/core-api/pyproject.toml`
- Create: `services/core-api/src/core_api/__init__.py` (e subpacotes)
- Create: `services/core-api/src/core_api/settings.py`
- Create: `services/core-api/src/core_api/main.py`
- Test: `services/core-api/tests/test_health.py`

- [ ] **Step 1: Estrutura e pyproject**

```bash
mkdir -p services/core-api/src/core_api/{auth,profile,foods,pantry,recipes,scoring,db} \
         services/core-api/{tests,seeds,alembic}
touch services/core-api/src/core_api/__init__.py \
      services/core-api/src/core_api/{auth,profile,foods,pantry,recipes,scoring,db}/__init__.py
```

`services/core-api/pyproject.toml`:

```toml
[project]
name = "core-api"
version = "1.0.0"
description = "Helfy — API de produto: auth, perfil, alimentos, dispensa, score e receitas"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111",
    "uvicorn[standard]>=0.29",
    "pydantic>=2.7",
    "pydantic-settings>=2.2",
    "sqlalchemy>=2.0",
    "psycopg[binary]>=3.1",
    "alembic>=1.13",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "bcrypt>=4.0,<4.1",
    "httpx>=0.27",
]

[dependency-groups]
dev = ["pytest>=8", "respx>=0.21", "ruff>=0.4"]

[tool.pytest.ini_options]
pythonpath = ["src", "."]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
src = ["src", "tests"]
```

(Pin `bcrypt<4.1` evita o aviso de incompatibilidade conhecido com passlib 1.7.)

- [ ] **Step 2: Escrever teste do /health**

`services/core-api/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from core_api.main import app


def test_health():
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_openapi_is_generated():
    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.json()["info"]["title"] == "Helfy Core API"
```

- [ ] **Step 3: Rodar e ver falhar**

```bash
cd services/core-api && uv sync && uv run pytest tests/test_health.py -v
```

Expected: FAIL — `ModuleNotFoundError: core_api.main`.

- [ ] **Step 4: Implementar settings.py e main.py**

`services/core-api/src/core_api/settings.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://helfy:helfy@localhost:5432/helfy"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24
    score_engine_url: str = "http://localhost:8001"
    score_cache_ttl_hours: int = 24  # TTL do cache food_scores (spec §5)
    off_base_url: str = "https://world.openfoodfacts.org"

    model_config = SettingsConfigDict(env_prefix="CORE_", env_file=".env", extra="ignore")


settings = Settings()
```

`services/core-api/src/core_api/main.py`:

```python
"""Helfy Core API — Swagger em /docs, ReDoc em /redoc (spec §7)."""
from fastapi import FastAPI

app = FastAPI(
    title="Helfy Core API",
    description="API de produto do Helfy: autenticação, perfil de saúde, alimentos, "
                "dispensa digital, score nutricional e receitas sugeridas.",
    version="1.0.0",
)
# Routers dos domínios são incluídos nas tasks seguintes, conforme cada módulo nasce.


@app.get("/health", tags=["system"], summary="Status do serviço")
def health() -> dict:
    return {"status": "ok"}
```

- [ ] **Step 5: Rodar, ver passar e commitar**

```bash
uv run pytest tests/test_health.py -v   # Expected: 2 PASSED
git add services/core-api
git commit -m "feat(core-api): scaffold do serviço com settings e health check"
```

---

### Task 2: Camada de banco — modelos SQLAlchemy e fixture de testes

**Files:**
- Create: `services/core-api/src/core_api/db/base.py`
- Create: `services/core-api/src/core_api/db/models.py`
- Create: `services/core-api/src/core_api/db/session.py`
- Create: `services/core-api/tests/conftest.py`
- Test: `services/core-api/tests/test_models.py`

- [ ] **Step 1: Subir o postgres e criar o banco de teste**

```bash
cd /home/bcr/estudos/helfy && docker compose up -d postgres
docker compose exec postgres createdb -U helfy helfy_test || true
```

- [ ] **Step 2: Escrever teste dos modelos**

`services/core-api/tests/test_models.py`:

```python
import uuid

from core_api.db.models import Food, PantryItem, Profile, Recipe, RecipeIngredient, User


def test_full_schema_roundtrip(db):
    user = User(email="a@b.com", password_hash="x", name="Ana")
    db.add(user)
    db.flush()

    db.add(Profile(user_id=user.id, age=30, height_cm=170.0, weight_kg=80.0,
                   goal="EMAGRECER", diet_type="vegetarian",
                   restrictions=["low_sugar"], allergies=["lactose"], preferences=[]))

    food = Food(name="Iogurte natural", barcode="789100", food_group="dairy",
                nutrition={"energy_kcal_100g": 61.0}, allergen_flags=["lactose"],
                flags=["animal_product"], source="OFF")
    db.add(food)
    db.flush()

    db.add(PantryItem(user_id=user.id, food_id=food.id))
    recipe = Recipe(name="Iogurte com frutas", instructions="Misture tudo.",
                    nutrition_total={})
    db.add(recipe)
    db.flush()
    db.add(RecipeIngredient(recipe_id=recipe.id, food_id=food.id, quantity="1 pote"))
    db.commit()

    loaded = db.get(User, user.id)
    assert loaded.profile.goal == "EMAGRECER"
    assert isinstance(loaded.id, uuid.UUID)
```

- [ ] **Step 3: Escrever conftest.py**

`services/core-api/tests/conftest.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core_api.db.base import Base

TEST_DATABASE_URL = "postgresql+psycopg://helfy:helfy@localhost:5432/helfy_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSession = sessionmaker(bind=engine, autoflush=False)


@pytest.fixture()
def db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    """TestClient com o banco de teste injetado no app."""
    from fastapi.testclient import TestClient

    from core_api.db.session import get_db
    from core_api.main import app

    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 4: Rodar e ver falhar**

```bash
cd services/core-api && uv run pytest tests/test_models.py -v
```

Expected: FAIL — `ModuleNotFoundError: core_api.db.models`.

- [ ] **Step 5: Implementar base.py, models.py e session.py**

`services/core-api/src/core_api/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

`services/core-api/src/core_api/db/models.py`:

```python
"""
Schema do Helfy (SCRUM-20, spec §5).

Enums de domínio (goal, diet_type, source...) são colunas String validadas na
borda Pydantic — evita migrations a cada novo valor durante a sprint.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core_api.db.base import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())
    profile: Mapped["Profile | None"] = relationship(back_populates="user",
                                                     cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                               primary_key=True)
    age: Mapped[int | None] = mapped_column(Integer)
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    goal: Mapped[str | None] = mapped_column(String(20))           # EMAGRECER|GANHAR_MASSA|MANTER
    diet_type: Mapped[str | None] = mapped_column(String(20))
    activity_level: Mapped[str | None] = mapped_column(String(20))
    cholesterol: Mapped[int | None] = mapped_column(Integer)
    glucose: Mapped[int | None] = mapped_column(Integer)
    restrictions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    preferences: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    allergies: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now(),
                                                 onupdate=func.now())
    user: Mapped[User] = relationship(back_populates="profile")


class Food(Base):
    __tablename__ = "foods"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          default=uuid.uuid4)
    barcode: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    food_group: Mapped[str] = mapped_column(String(40), default="other")
    nutrition: Mapped[dict] = mapped_column(JSONB, default=dict)
    allergen_flags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    flags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)  # animal_product|meat|fish
    source: Mapped[str] = mapped_column(String(10), default="MANUAL")      # OFF|MANUAL|SEED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())


class PantryItem(Base):
    __tablename__ = "pantry_items"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                               primary_key=True)
    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"),
                                               primary_key=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(10, 2))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())


class Recipe(Base):
    __tablename__ = "recipes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True,
                                          default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    instructions: Mapped[str] = mapped_column(Text)
    nutrition_total: Mapped[dict] = mapped_column(JSONB, default=dict)
    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        cascade="all, delete-orphan")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True)
    food_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), primary_key=True)
    quantity: Mapped[str | None] = mapped_column(String(60))  # texto livre: "2 xícaras"


class FoodScore(Base):
    __tablename__ = "food_scores"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
                                               primary_key=True)
    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"),
                                               primary_key=True)
    score: Mapped[float] = mapped_column(Numeric(4, 3))
    breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)
    model_version: Mapped[str] = mapped_column(String(20))
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now())
```

`services/core-api/src/core_api/db/session.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core_api.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 6: Rodar, ver passar e commitar**

```bash
uv run pytest tests/test_models.py -v   # Expected: 1 PASSED
git add src/core_api/db tests/
git commit -m "feat(core-api): modelos do banco (SCRUM-20) e fixture de testes com postgres"
```

---

### Task 3: Alembic — migração inicial

**Files:**
- Create: `services/core-api/alembic.ini`, `services/core-api/alembic/env.py`, `services/core-api/alembic/versions/<hash>_schema_inicial.py`

- [ ] **Step 1: Inicializar o Alembic**

```bash
cd services/core-api && uv run alembic init alembic
```

- [ ] **Step 2: Configurar env.py para usar settings e os modelos**

Em `alembic/env.py`, substituir o bloco de configuração por:

```python
from core_api.db.base import Base
from core_api.db import models  # noqa: F401 — registra as tabelas no metadata
from core_api.settings import settings

config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata
```

E em `alembic.ini`, comentar/remover a linha `sqlalchemy.url = ...` (a URL vem das settings). Adicionar no topo de `env.py`, antes dos imports do projeto:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
```

- [ ] **Step 3: Gerar e aplicar a migração inicial**

```bash
uv run alembic revision --autogenerate -m "schema inicial: users, profiles, foods, pantry, recipes, food_scores"
uv run alembic upgrade head
uv run python -c "
from sqlalchemy import create_engine, inspect
from core_api.settings import settings
tables = inspect(create_engine(settings.database_url)).get_table_names()
expected = {'users','profiles','foods','pantry_items','recipes','recipe_ingredients','food_scores'}
missing = expected - set(tables)
assert not missing, missing
print('schema ok:', sorted(expected))
"
```

Expected: `schema ok: [...]` com as 7 tabelas. Revisar o arquivo gerado em `alembic/versions/` antes de aplicar (autogenerate às vezes erra ARRAY/JSONB).

- [ ] **Step 4: Commitar**

```bash
git add alembic.ini alembic/
git commit -m "feat(core-api): migração inicial do schema (SCRUM-20)"
```

---

### Task 4: Auth — registro, login e usuário atual (SCRUM-12)

**Files:**
- Create: `services/core-api/src/core_api/auth/security.py`
- Create: `services/core-api/src/core_api/auth/schemas.py`
- Create: `services/core-api/src/core_api/auth/routes.py`
- Create: `services/core-api/src/core_api/auth/deps.py`
- Modify: `services/core-api/src/core_api/main.py`
- Test: `services/core-api/tests/test_auth.py`

- [ ] **Step 1: Escrever testes**

`services/core-api/tests/test_auth.py`:

```python
REGISTER = {"email": "ana@helfy.app", "password": "s3nh4-forte", "name": "Ana"}


def test_register_creates_user(client):
    resp = client.post("/auth/register", json=REGISTER)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "ana@helfy.app"
    assert "password" not in body and "password_hash" not in body


def test_register_duplicate_email_409(client):
    client.post("/auth/register", json=REGISTER)
    resp = client.post("/auth/register", json=REGISTER)
    assert resp.status_code == 409


def test_login_returns_jwt(client):
    client.post("/auth/register", json=REGISTER)
    resp = client.post("/auth/login", json={"email": REGISTER["email"],
                                            "password": REGISTER["password"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"].count(".") == 2


def test_login_wrong_password_401(client):
    client.post("/auth/register", json=REGISTER)
    resp = client.post("/auth/login", json={"email": REGISTER["email"], "password": "errada"})
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(client):
    client.post("/auth/register", json=REGISTER)
    token = client.post("/auth/login", json={"email": REGISTER["email"],
                                             "password": REGISTER["password"]}).json()["access_token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == REGISTER["email"]
```

- [ ] **Step 2: Rodar e ver falhar**

```bash
uv run pytest tests/test_auth.py -v
```

Expected: FAIL — 404 nas rotas (`/auth/...` não existe).

- [ ] **Step 3: Implementar security.py, schemas.py, deps.py e routes.py**

`services/core-api/src/core_api/auth/security.py`:

```python
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from core_api.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expires_minutes)
    return jwt.encode({"sub": user_id, "exp": expires},
                      settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str | None:
    """Retorna o user_id (sub) ou None se inválido/expirado."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None
```

`services/core-api/src/core_api/auth/schemas.py`:

```python
from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=120)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    name: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

(`EmailStr` requer `email-validator`: adicionar `"email-validator>=2.0"` às dependencies do pyproject e rodar `uv sync`.)

`services/core-api/src/core_api/auth/deps.py`:

```python
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
```

`services/core-api/src/core_api/auth/routes.py`:

```python
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
```

Em `main.py`, incluir o router:

```python
from core_api.auth.routes import router as auth_router

app.include_router(auth_router)
```

- [ ] **Step 4: Rodar, ver passar e commitar**

```bash
uv run pytest tests/test_auth.py -v   # Expected: 6 PASSED
git add src/core_api/auth src/core_api/main.py pyproject.toml uv.lock tests/test_auth.py
git commit -m "feat(core-api): cadastro, login e autenticação JWT (SCRUM-12)"
```

---

### Task 5: Perfil — GET/PUT com invalidação do cache de scores (SCRUM-13)

**Files:**
- Create: `services/core-api/src/core_api/profile/schemas.py`
- Create: `services/core-api/src/core_api/profile/routes.py`
- Modify: `services/core-api/src/core_api/main.py`
- Test: `services/core-api/tests/test_profile.py`
- Create: `services/core-api/tests/helpers.py`

- [ ] **Step 1: Criar helper de autenticação para testes**

`services/core-api/tests/helpers.py`:

```python
def auth_headers(client, email="user@helfy.app", password="s3nh4-forte", name="User"):
    """Registra (se preciso), loga e retorna (headers, user_id)."""
    reg = client.post("/auth/register",
                      json={"email": email, "password": password, "name": name})
    user_id = reg.json().get("id")
    token = client.post("/auth/login",
                        json={"email": email, "password": password}).json()["access_token"]
    if user_id is None:  # usuário já existia; descobre o id via /auth/me
        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        user_id = me.json()["id"]
    return {"Authorization": f"Bearer {token}"}, user_id
```

- [ ] **Step 2: Escrever testes do perfil**

`services/core-api/tests/test_profile.py`:

```python
import uuid

from core_api.db.models import Food, FoodScore

from tests.helpers import auth_headers

PROFILE = {
    "age": 30, "height_cm": 170.0, "weight_kg": 80.0,
    "goal": "EMAGRECER", "diet_type": "vegetarian", "activity_level": "lightly_active",
    "cholesterol": 210, "glucose": 110,
    "restrictions": ["low_sugar"], "preferences": ["doces"], "allergies": ["lactose"],
}


def test_put_creates_and_get_returns_profile(client):
    headers, user_id = auth_headers(client)
    resp = client.put(f"/perfil/{user_id}", json=PROFILE, headers=headers)
    assert resp.status_code == 200

    resp = client.get(f"/perfil/{user_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["goal"] == "EMAGRECER"
    assert body["allergies"] == ["lactose"]


def test_get_profile_before_creation_404(client):
    headers, user_id = auth_headers(client)
    assert client.get(f"/perfil/{user_id}", headers=headers).status_code == 404


def test_cannot_access_other_users_profile(client):
    headers_a, _ = auth_headers(client, email="a@helfy.app")
    _, user_b = auth_headers(client, email="b@helfy.app")
    assert client.get(f"/perfil/{user_b}", headers=headers_a).status_code == 403


def test_invalid_goal_422(client):
    headers, user_id = auth_headers(client)
    resp = client.put(f"/perfil/{user_id}", json={**PROFILE, "goal": "FICAR_FORTE"},
                      headers=headers)
    assert resp.status_code == 422


def test_put_profile_invalidates_score_cache(client, db):
    headers, user_id = auth_headers(client)
    client.put(f"/perfil/{user_id}", json=PROFILE, headers=headers)

    food = Food(name="Maçã", food_group="fruit", nutrition={}, source="MANUAL")
    db.add(food)
    db.flush()
    db.add(FoodScore(user_id=uuid.UUID(user_id), food_id=food.id,
                     score=0.9, breakdown={}, model_version="mlp-v1"))
    db.commit()

    client.put(f"/perfil/{user_id}", json={**PROFILE, "goal": "MANTER"}, headers=headers)
    assert db.query(FoodScore).filter_by(user_id=uuid.UUID(user_id)).count() == 0
```

- [ ] **Step 3: Rodar e ver falhar**

```bash
uv run pytest tests/test_profile.py -v
```

Expected: FAIL — 404 (rotas de perfil não existem).

- [ ] **Step 4: Implementar schemas.py e routes.py**

`services/core-api/src/core_api/profile/schemas.py`:

```python
from typing import Literal

from pydantic import BaseModel, Field

Goal = Literal["EMAGRECER", "GANHAR_MASSA", "MANTER"]
DietType = Literal["omnivore", "vegetarian", "vegan", "keto", "pescatarian", "paleo"]
ActivityLevel = Literal["sedentary", "lightly_active", "moderately_active", "very_active"]
Allergen = Literal["gluten", "lactose", "nuts", "shellfish", "eggs", "soy"]
Restriction = Literal["low_sodium", "low_sugar", "low_fat", "high_protein", "low_carb"]

PROFILE_EXAMPLE = {
    "age": 30, "height_cm": 170.0, "weight_kg": 80.0,
    "goal": "EMAGRECER", "diet_type": "vegetarian", "activity_level": "lightly_active",
    "cholesterol": 210, "glucose": 110,
    "restrictions": ["low_sugar"], "preferences": ["doces"], "allergies": ["lactose"],
}


class ProfileIn(BaseModel):
    age: int = Field(ge=18, le=110)
    height_cm: float = Field(gt=100, le=250)
    weight_kg: float = Field(gt=30, le=300)
    goal: Goal
    diet_type: DietType = "omnivore"
    activity_level: ActivityLevel = "lightly_active"
    cholesterol: int | None = Field(default=None, ge=100, le=400)
    glucose: int | None = Field(default=None, ge=40, le=500,
                                description="Glicemia de jejum em mg/dL")
    restrictions: list[Restriction] = []
    preferences: list[str] = []
    allergies: list[Allergen] = []

    model_config = {"json_schema_extra": {"examples": [PROFILE_EXAMPLE]}}


class ProfileOut(ProfileIn):
    user_id: str
```

`services/core-api/src/core_api/profile/routes.py`:

```python
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
```

Em `main.py`:

```python
from core_api.profile.routes import router as profile_router

app.include_router(profile_router)
```

- [ ] **Step 5: Rodar, ver passar e commitar**

```bash
uv run pytest tests/test_profile.py -v   # Expected: 5 PASSED
git add src/core_api/profile src/core_api/main.py tests/
git commit -m "feat(core-api): perfil de saúde com invalidação do cache de scores (SCRUM-13)"
```

---

### Task 6: Alimentos — Open Food Facts, barcode e input manual (SCRUM-14/15/16)

**Files:**
- Create: `services/core-api/src/core_api/foods/off_client.py`
- Create: `services/core-api/src/core_api/foods/schemas.py`
- Create: `services/core-api/src/core_api/foods/routes.py`
- Modify: `services/core-api/src/core_api/main.py`
- Test: `services/core-api/tests/test_foods.py`

- [ ] **Step 1: Escrever testes (OFF mockado com respx)**

`services/core-api/tests/test_foods.py`:

```python
import respx
from httpx import Response

from core_api.foods.off_client import normalize_off_product
from core_api.settings import settings

from tests.helpers import auth_headers

OFF_PRODUCT = {
    "status": 1,
    "product": {
        "product_name": "Iogurte Natural Integral",
        "categories_tags": ["en:dairies", "en:yogurts"],
        "allergens_tags": ["en:milk"],
        "nutriments": {
            "energy-kcal_100g": 61.0, "proteins_100g": 3.3, "carbohydrates_100g": 4.7,
            "fat_100g": 3.3, "saturated-fat_100g": 1.9, "fiber_100g": 0.0,
            "sodium_100g": 0.04, "sugars_100g": 4.7,
        },
    },
}


def test_normalize_off_product_maps_fields():
    food = normalize_off_product("7891000100103", OFF_PRODUCT["product"])
    assert food["name"] == "Iogurte Natural Integral"
    assert food["food_group"] == "dairy"
    assert food["allergen_flags"] == ["lactose"]
    assert food["flags"] == ["animal_product"]
    assert food["nutrition"]["sodium_mg_100g"] == 40.0  # OFF dá sódio em g → mg
    assert food["nutrition"]["sugar_100g"] == 4.7       # sugars_100g → sugar_100g


@respx.mock
def test_barcode_miss_fetches_from_off_and_persists(client):
    headers, _ = auth_headers(client)
    respx.get(f"{settings.off_base_url}/api/v2/product/7891000100103.json").mock(
        return_value=Response(200, json=OFF_PRODUCT))

    resp = client.get("/alimentos/barcode/7891000100103", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["source"] == "OFF"

    # Segunda chamada: cache local, sem novo hit no OFF
    respx.calls.assert_called_once()
    resp2 = client.get("/alimentos/barcode/7891000100103", headers=headers)
    assert resp2.status_code == 200
    assert respx.calls.call_count == 1


@respx.mock
def test_barcode_not_found_in_off_404(client):
    headers, _ = auth_headers(client)
    respx.get(f"{settings.off_base_url}/api/v2/product/000.json").mock(
        return_value=Response(200, json={"status": 0}))
    assert client.get("/alimentos/barcode/000", headers=headers).status_code == 404


@respx.mock
def test_off_unavailable_502(client):
    headers, _ = auth_headers(client)
    respx.get(f"{settings.off_base_url}/api/v2/product/111.json").mock(
        side_effect=Exception("timeout"))
    assert client.get("/alimentos/barcode/111", headers=headers).status_code == 502


def test_manual_food_creation_and_get(client):
    headers, _ = auth_headers(client)
    resp = client.post("/alimentos", headers=headers, json={
        "name": "Arroz integral caseiro", "food_group": "grain",
        "nutrition": {"energy_kcal_100g": 124.0, "proteins_100g": 2.6,
                      "carbohydrates_100g": 25.8, "fat_100g": 1.0,
                      "saturated_fat_100g": 0.3, "fiber_100g": 2.7,
                      "sodium_mg_100g": 1.0, "sugar_100g": 0.4},
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["source"] == "MANUAL"

    resp = client.get(f"/alimentos/{body['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Arroz integral caseiro"
```

- [ ] **Step 2: Rodar e ver falhar**

```bash
uv run pytest tests/test_foods.py -v
```

Expected: FAIL — `ModuleNotFoundError: core_api.foods.off_client`.

- [ ] **Step 3: Implementar off_client.py**

`services/core-api/src/core_api/foods/off_client.py`:

```python
"""
Cliente do Open Food Facts (SCRUM-14) e normalização para o formato canônico
do Helfy (mesmas chaves de nutrition que a score-engine espera).
"""
import logging

import httpx

from core_api.settings import settings

logger = logging.getLogger(__name__)

# allergens_tags do OFF → alérgenos canônicos do Helfy
OFF_ALLERGEN_MAP = {
    "en:gluten": "gluten", "en:milk": "lactose", "en:nuts": "nuts",
    "en:peanuts": "nuts", "en:crustaceans": "shellfish", "en:fish": "shellfish",
    "en:eggs": "eggs", "en:soybeans": "soy",
}

# primeira categoria que casar define o food_group (ordem importa: específico → genérico)
OFF_FOOD_GROUP_KEYWORDS = [
    ("meat", "meat"), ("poultry", "meat"), ("fishes", "fish"), ("seafood", "fish"),
    ("dairies", "dairy"), ("cheeses", "dairy"), ("yogurts", "dairy"),
    ("fruits", "fruit"), ("vegetables", "vegetable"), ("legumes", "legume"),
    ("cereals", "grain"), ("breads", "grain"), ("pastas", "grain"),
    ("snacks", "snack"), ("beverages", "beverage"), ("eggs", "egg"),
]

ANIMAL_GROUPS = {"meat", "fish", "dairy", "egg"}


def _food_group_from_categories(categories: list[str]) -> str:
    for keyword, group in OFF_FOOD_GROUP_KEYWORDS:
        if any(keyword in cat for cat in categories):
            return group
    return "other"


def normalize_off_product(barcode: str, product: dict) -> dict:
    """Converte um produto do OFF para o dict canônico do Food do Helfy."""
    nutriments = product.get("nutriments") or {}
    nutrition = {
        "energy_kcal_100g": float(nutriments.get("energy-kcal_100g") or 0),
        "proteins_100g": float(nutriments.get("proteins_100g") or 0),
        "carbohydrates_100g": float(nutriments.get("carbohydrates_100g") or 0),
        "fat_100g": float(nutriments.get("fat_100g") or 0),
        "saturated_fat_100g": float(nutriments.get("saturated-fat_100g") or 0),
        "fiber_100g": float(nutriments.get("fiber_100g") or 0),
        "sodium_mg_100g": float(nutriments.get("sodium_100g") or 0) * 1000.0,  # g → mg
        "sugar_100g": float(nutriments.get("sugars_100g") or 0),
    }
    allergens = sorted({OFF_ALLERGEN_MAP[tag]
                        for tag in product.get("allergens_tags") or []
                        if tag in OFF_ALLERGEN_MAP})
    food_group = _food_group_from_categories(product.get("categories_tags") or [])

    flags = []
    if food_group in ANIMAL_GROUPS:
        flags.append("animal_product")
    if food_group == "meat":
        flags.append("meat")
    if food_group == "fish":
        flags.append("fish")

    return {
        "barcode": barcode,
        "name": product.get("product_name") or f"Produto {barcode}",
        "food_group": food_group,
        "nutrition": nutrition,
        "allergen_flags": allergens,
        "flags": flags,
        "source": "OFF",
    }


class OffUnavailableError(Exception):
    pass


def fetch_product(barcode: str) -> dict | None:
    """Busca no OFF. Retorna o dict normalizado, None se não existe, ou levanta
    OffUnavailableError em falha de rede/timeout."""
    url = f"{settings.off_base_url}/api/v2/product/{barcode}.json"
    try:
        resp = httpx.get(url, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Open Food Facts indisponível para %s: %s", barcode, exc)
        raise OffUnavailableError(str(exc)) from exc
    if data.get("status") != 1:
        return None
    return normalize_off_product(barcode, data["product"])
```

- [ ] **Step 4: Implementar schemas.py e routes.py**

`services/core-api/src/core_api/foods/schemas.py`:

```python
from pydantic import BaseModel, Field

NUTRITION_KEYS_DOC = ("energy_kcal_100g, proteins_100g, carbohydrates_100g, fat_100g, "
                      "saturated_fat_100g, fiber_100g, sodium_mg_100g, sugar_100g")


class FoodManualIn(BaseModel):
    """Input manual de produto (SCRUM-15)."""
    name: str = Field(min_length=1, max_length=255)
    food_group: str = "other"
    nutrition: dict[str, float] = Field(default_factory=dict,
                                        description=f"Por 100g. Chaves: {NUTRITION_KEYS_DOC}")
    allergen_flags: list[str] = []
    flags: list[str] = []


class FoodOut(BaseModel):
    id: str
    barcode: str | None
    name: str
    food_group: str
    nutrition: dict[str, float]
    allergen_flags: list[str]
    flags: list[str]
    source: str
```

`services/core-api/src/core_api/foods/routes.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from core_api.auth.deps import get_current_user
from core_api.db.models import Food
from core_api.db.session import get_db
from core_api.foods.off_client import OffUnavailableError, fetch_product
from core_api.foods.schemas import FoodManualIn, FoodOut

router = APIRouter(prefix="/alimentos", tags=["foods"],
                   dependencies=[Depends(get_current_user)])


def _to_out(food: Food) -> FoodOut:
    return FoodOut(id=str(food.id), barcode=food.barcode, name=food.name,
                   food_group=food.food_group, nutrition=food.nutrition,
                   allergen_flags=food.allergen_flags, flags=food.flags,
                   source=food.source)


@router.get("/barcode/{codigo}", response_model=FoodOut,
            summary="Busca alimento por código de barras (cache local → Open Food Facts)")
def get_by_barcode(codigo: str, db: Session = Depends(get_db)) -> FoodOut:
    food = db.scalar(select(Food).where(Food.barcode == codigo))
    if food is not None:
        return _to_out(food)

    try:
        normalized = fetch_product(codigo)
    except OffUnavailableError:
        raise HTTPException(status_code=502,
                            detail="Base de produtos externa indisponível; tente o input manual")
    if normalized is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado na base externa")

    food = Food(**normalized)
    db.add(food)
    db.commit()
    return _to_out(food)


@router.post("", response_model=FoodOut, status_code=201,
             summary="Cadastra alimento manualmente")
def create_manual(body: FoodManualIn, db: Session = Depends(get_db)) -> FoodOut:
    food = Food(name=body.name, food_group=body.food_group, nutrition=body.nutrition,
                allergen_flags=body.allergen_flags, flags=body.flags, source="MANUAL")
    db.add(food)
    db.commit()
    return _to_out(food)


@router.get("/{alimento_id}", response_model=FoodOut, summary="Busca alimento por id")
def get_by_id(alimento_id: uuid.UUID, db: Session = Depends(get_db)) -> FoodOut:
    food = db.get(Food, alimento_id)
    if food is None:
        raise HTTPException(status_code=404, detail="Alimento não encontrado")
    return _to_out(food)
```

Em `main.py`:

```python
from core_api.foods.routes import router as foods_router

app.include_router(foods_router)
```

Atenção à ordem das rotas: `/barcode/{codigo}` deve ser declarada antes de `/{alimento_id}` (como acima), senão "barcode" é interpretado como UUID e dá 422.

- [ ] **Step 5: Rodar, ver passar e commitar**

```bash
uv run pytest tests/test_foods.py -v   # Expected: 6 PASSED
git add src/core_api/foods src/core_api/main.py tests/test_foods.py
git commit -m "feat(core-api): base de produtos com Open Food Facts e input manual (SCRUM-14/15/16)"
```

---

### Task 7: Dispensa digital (SCRUM-21)

**Files:**
- Create: `services/core-api/src/core_api/pantry/schemas.py`
- Create: `services/core-api/src/core_api/pantry/routes.py`
- Modify: `services/core-api/src/core_api/main.py`
- Test: `services/core-api/tests/test_pantry.py`

- [ ] **Step 1: Escrever testes**

`services/core-api/tests/test_pantry.py`:

```python
from core_api.db.models import Food

from tests.helpers import auth_headers


def _seed_food(db, name="Banana", barcode=None):
    food = Food(name=name, barcode=barcode, food_group="fruit",
                nutrition={"energy_kcal_100g": 89.0}, source="MANUAL")
    db.add(food)
    db.commit()
    return str(food.id)


def test_add_by_food_id_and_list(client, db):
    headers, user_id = auth_headers(client)
    food_id = _seed_food(db)

    resp = client.post(f"/dispensa/{user_id}/adicionar", headers=headers,
                       json={"alimento_id": food_id, "quantidade": 3})
    assert resp.status_code == 201

    resp = client.get(f"/dispensa/{user_id}", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["food"]["name"] == "Banana"
    assert items[0]["quantidade"] == 3


def test_add_by_barcode_uses_local_food(client, db):
    headers, user_id = auth_headers(client)
    _seed_food(db, name="Iogurte", barcode="789100")

    resp = client.post(f"/dispensa/{user_id}/adicionar", headers=headers,
                       json={"codigo_barras": "789100"})
    assert resp.status_code == 201
    items = client.get(f"/dispensa/{user_id}", headers=headers).json()
    assert items[0]["food"]["name"] == "Iogurte"


def test_add_same_food_twice_updates_quantity(client, db):
    headers, user_id = auth_headers(client)
    food_id = _seed_food(db)
    client.post(f"/dispensa/{user_id}/adicionar", headers=headers,
                json={"alimento_id": food_id, "quantidade": 1})
    client.post(f"/dispensa/{user_id}/adicionar", headers=headers,
                json={"alimento_id": food_id, "quantidade": 5})
    items = client.get(f"/dispensa/{user_id}", headers=headers).json()
    assert len(items) == 1
    assert items[0]["quantidade"] == 5


def test_remove_food(client, db):
    headers, user_id = auth_headers(client)
    food_id = _seed_food(db)
    client.post(f"/dispensa/{user_id}/adicionar", headers=headers,
                json={"alimento_id": food_id})
    resp = client.delete(f"/dispensa/{user_id}/{food_id}", headers=headers)
    assert resp.status_code == 204
    assert client.get(f"/dispensa/{user_id}", headers=headers).json() == []


def test_other_users_pantry_403(client, db):
    headers_a, _ = auth_headers(client, email="a@helfy.app")
    _, user_b = auth_headers(client, email="b@helfy.app")
    assert client.get(f"/dispensa/{user_b}", headers=headers_a).status_code == 403
```

- [ ] **Step 2: Rodar e ver falhar**

```bash
uv run pytest tests/test_pantry.py -v
```

Expected: FAIL — 404 nas rotas.

- [ ] **Step 3: Implementar schemas.py e routes.py**

`services/core-api/src/core_api/pantry/schemas.py`:

```python
from pydantic import BaseModel, model_validator

from core_api.foods.schemas import FoodOut


class PantryAddIn(BaseModel):
    """Adiciona por id OU por código de barras (exatamente um dos dois)."""
    alimento_id: str | None = None
    codigo_barras: str | None = None
    quantidade: float | None = None

    @model_validator(mode="after")
    def exactly_one_identifier(self):
        if bool(self.alimento_id) == bool(self.codigo_barras):
            raise ValueError("Informe alimento_id OU codigo_barras")
        return self


class PantryItemOut(BaseModel):
    food: FoodOut
    quantidade: float | None
```

`services/core-api/src/core_api/pantry/routes.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from core_api.auth.deps import get_current_user, require_owner
from core_api.db.models import Food, PantryItem, User
from core_api.db.session import get_db
from core_api.foods.off_client import OffUnavailableError, fetch_product
from core_api.foods.routes import _to_out as food_to_out
from core_api.pantry.schemas import PantryAddIn, PantryItemOut

router = APIRouter(prefix="/dispensa", tags=["pantry"])


def _resolve_food(body: PantryAddIn, db: Session) -> Food:
    if body.alimento_id:
        food = db.get(Food, uuid.UUID(body.alimento_id))
        if food is None:
            raise HTTPException(status_code=404, detail="Alimento não encontrado")
        return food
    food = db.scalar(select(Food).where(Food.barcode == body.codigo_barras))
    if food is not None:
        return food
    try:  # mesmo fluxo do GET /alimentos/barcode: miss local → Open Food Facts
        normalized = fetch_product(body.codigo_barras)
    except OffUnavailableError:
        raise HTTPException(status_code=502, detail="Base de produtos externa indisponível")
    if normalized is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado na base externa")
    food = Food(**normalized)
    db.add(food)
    db.flush()
    return food


@router.get("/{usuario_id}", response_model=list[PantryItemOut],
            summary="Lista a dispensa do usuário")
def list_pantry(usuario_id: uuid.UUID, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)) -> list[PantryItemOut]:
    require_owner(user, usuario_id)
    rows = db.execute(
        select(PantryItem, Food).join(Food, PantryItem.food_id == Food.id)
        .where(PantryItem.user_id == usuario_id).order_by(Food.name)
    ).all()
    return [PantryItemOut(food=food_to_out(food),
                          quantidade=float(item.quantity) if item.quantity is not None else None)
            for item, food in rows]


@router.post("/{usuario_id}/adicionar", response_model=PantryItemOut, status_code=201,
             summary="Adiciona alimento à dispensa por id ou código de barras")
def add_item(usuario_id: uuid.UUID, body: PantryAddIn,
             user: User = Depends(get_current_user),
             db: Session = Depends(get_db)) -> PantryItemOut:
    require_owner(user, usuario_id)
    food = _resolve_food(body, db)
    item = db.get(PantryItem, (usuario_id, food.id))
    if item is None:
        item = PantryItem(user_id=usuario_id, food_id=food.id)
        db.add(item)
    item.quantity = body.quantidade
    db.commit()
    return PantryItemOut(food=food_to_out(food), quantidade=body.quantidade)


@router.delete("/{usuario_id}/{alimento_id}", status_code=204,
               summary="Remove alimento da dispensa")
def remove_item(usuario_id: uuid.UUID, alimento_id: uuid.UUID,
                user: User = Depends(get_current_user),
                db: Session = Depends(get_db)) -> Response:
    require_owner(user, usuario_id)
    item = db.get(PantryItem, (usuario_id, alimento_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Item não está na dispensa")
    db.delete(item)
    db.commit()
    return Response(status_code=204)
```

Em `main.py`:

```python
from core_api.pantry.routes import router as pantry_router

app.include_router(pantry_router)
```

- [ ] **Step 4: Rodar, ver passar e commitar**

```bash
uv run pytest tests/test_pantry.py -v   # Expected: 5 PASSED
git add src/core_api/pantry src/core_api/main.py tests/test_pantry.py
git commit -m "feat(core-api): API da dispensa digital (SCRUM-21)"
```

---

### Task 8: Scoring — cliente da engine, cache TTL 24h e POST /score público (SCRUM-18 na borda do produto)

**Files:**
- Create: `services/core-api/src/core_api/scoring/engine_client.py`
- Create: `services/core-api/src/core_api/scoring/service.py`
- Create: `services/core-api/src/core_api/scoring/routes.py`
- Modify: `services/core-api/src/core_api/main.py`
- Test: `services/core-api/tests/test_scoring.py`

- [ ] **Step 1: Escrever testes**

`services/core-api/tests/test_scoring.py`:

```python
import uuid
from datetime import datetime, timedelta, timezone

import respx
from httpx import Response

from core_api.db.models import Food, FoodScore
from core_api.settings import settings

from tests.helpers import auth_headers
from tests.test_profile import PROFILE

ENGINE_URL = f"{settings.score_engine_url}/score"


def _engine_response(food_ids, score=0.8):
    return {"scores": [{"food_id": fid, "score": score,
                        "breakdown": {"allergen_safe": True, "diet_compatible": True,
                                      "goal_alignment": "high", "health_flags": [],
                                      "heuristic_reference": 8.0}}
                       for fid in food_ids],
            "model_version": "mlp-v1", "engine": "mlp"}


def _setup_user_with_food(client, db, email="user@helfy.app"):
    headers, user_id = auth_headers(client, email=email)
    client.put(f"/perfil/{user_id}", json=PROFILE, headers=headers)
    food = Food(name="Aveia", food_group="grain",
                nutrition={"energy_kcal_100g": 389.0}, source="MANUAL")
    db.add(food)
    db.commit()
    return headers, user_id, str(food.id)


@respx.mock
def test_score_endpoint_calls_engine_and_caches(client, db):
    headers, user_id, food_id = _setup_user_with_food(client, db)
    route = respx.post(ENGINE_URL).mock(
        return_value=Response(200, json=_engine_response([food_id])))

    resp = client.post("/score", headers=headers,
                       json={"usuario_id": user_id, "alimento_ids": [food_id]})
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["alimento_id"] == food_id
    assert body[0]["score"] == 0.8
    assert isinstance(body[0]["justificativa"], str)

    # Segunda chamada: vem do cache, engine não é chamada de novo
    client.post("/score", headers=headers,
                json={"usuario_id": user_id, "alimento_ids": [food_id]})
    assert route.call_count == 1
    assert db.query(FoodScore).count() == 1


@respx.mock
def test_expired_cache_entry_is_recomputed(client, db):
    headers, user_id, food_id = _setup_user_with_food(client, db)
    stale = datetime.now(timezone.utc) - timedelta(hours=25)  # além do TTL de 24h
    db.add(FoodScore(user_id=uuid.UUID(user_id), food_id=uuid.UUID(food_id),
                     score=0.1, breakdown={}, model_version="mlp-v1", computed_at=stale))
    db.commit()

    route = respx.post(ENGINE_URL).mock(
        return_value=Response(200, json=_engine_response([food_id], score=0.9)))
    resp = client.post("/score", headers=headers,
                       json={"usuario_id": user_id, "alimento_ids": [food_id]})
    assert route.call_count == 1            # recalculou
    assert resp.json()[0]["score"] == 0.9


@respx.mock
def test_engine_down_returns_503(client, db):
    headers, user_id, food_id = _setup_user_with_food(client, db)
    respx.post(ENGINE_URL).mock(side_effect=Exception("connection refused"))
    resp = client.post("/score", headers=headers,
                       json={"usuario_id": user_id, "alimento_ids": [food_id]})
    assert resp.status_code == 503


def test_score_requires_profile(client, db):
    headers, user_id = auth_headers(client)
    food = Food(name="Maçã", food_group="fruit", nutrition={}, source="MANUAL")
    db.add(food)
    db.commit()
    resp = client.post("/score", headers=headers,
                       json={"usuario_id": user_id, "alimento_ids": [str(food.id)]})
    assert resp.status_code == 409  # perfil é pré-requisito para personalizar
```

- [ ] **Step 2: Rodar e ver falhar**

```bash
uv run pytest tests/test_scoring.py -v
```

Expected: FAIL — 404 na rota /score.

- [ ] **Step 3: Implementar engine_client.py e service.py**

`services/core-api/src/core_api/scoring/engine_client.py`:

```python
"""Cliente HTTP da score-engine (contrato do Plano 1)."""
import httpx

from core_api.db.models import Food, Profile
from core_api.settings import settings


class EngineUnavailableError(Exception):
    pass


def _profile_payload(profile: Profile) -> dict:
    return {
        "goal": profile.goal,
        "diet_type": profile.diet_type or "omnivore",
        "activity_level": profile.activity_level or "lightly_active",
        "age": profile.age,
        "weight_kg": profile.weight_kg,
        "height_cm": profile.height_cm,
        "total_cholesterol": profile.cholesterol,
        "glucose": profile.glucose,
        "allergies": profile.allergies or [],
        "restrictions": profile.restrictions or [],
    }


def _food_payload(food: Food) -> dict:
    return {
        "food_id": str(food.id),
        "food_group": food.food_group,
        "nutrition": food.nutrition or {},
        "allergen_flags": food.allergen_flags or [],
        "flags": food.flags or [],
    }


def score_foods(profile: Profile, foods: list[Food]) -> dict:
    """POST /score na engine. Retorna {food_id: {score, breakdown}} e a versão do modelo."""
    payload = {"profile": _profile_payload(profile),
               "foods": [_food_payload(f) for f in foods]}
    try:
        resp = httpx.post(f"{settings.score_engine_url}/score", json=payload, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise EngineUnavailableError(str(exc)) from exc
    return {
        "by_food": {item["food_id"]: item for item in data["scores"]},
        "model_version": data["model_version"],
    }
```

`services/core-api/src/core_api/scoring/service.py`:

```python
"""
Obtenção de scores com cache (tabela food_scores).

Política de cache (spec §5): hit válido = entrada com computed_at dentro do TTL
de 24h. Invalidação por evento acontece no PUT /perfil. Misses (incluindo
entradas expiradas) vão em lote para a engine e fazem upsert.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from core_api.db.models import Food, FoodScore, Profile
from core_api.scoring.engine_client import score_foods
from core_api.settings import settings


def justification_from_breakdown(breakdown: dict) -> str:
    """Transparência de resultado (SCRUM-19) em uma frase para o usuário."""
    if not breakdown.get("allergen_safe", True):
        return "Contém alérgeno presente no seu perfil"
    if not breakdown.get("diet_compatible", True):
        return "Incompatível com a sua dieta"
    if breakdown.get("health_flags"):
        return "Atenção: " + "; ".join(breakdown["health_flags"])
    alignment = breakdown.get("goal_alignment", "moderate")
    labels = {"high": "Forte alinhamento com o seu objetivo",
              "moderate": "Alinhamento moderado com o seu objetivo",
              "low": "Baixo alinhamento com o seu objetivo",
              "poor": "Pouco recomendado para o seu objetivo"}
    return labels.get(alignment, labels["moderate"])


def get_scores(db: Session, profile: Profile, foods: list[Food]) -> dict[str, dict]:
    """Retorna {food_id(str): {"score": float, "breakdown": dict}} para todos os foods.

    Levanta EngineUnavailableError se houver miss e a engine estiver fora."""
    user_id = profile.user_id
    food_ids = [f.id for f in foods]
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.score_cache_ttl_hours)

    cached = db.execute(
        select(FoodScore).where(FoodScore.user_id == user_id,
                                FoodScore.food_id.in_(food_ids),
                                FoodScore.computed_at >= cutoff)
    ).scalars().all()
    result = {str(row.food_id): {"score": float(row.score), "breakdown": row.breakdown}
              for row in cached}

    missing = [f for f in foods if str(f.id) not in result]
    if missing:
        engine_result = score_foods(profile, missing)
        now = datetime.now(timezone.utc)
        for food in missing:
            item = engine_result["by_food"][str(food.id)]
            result[str(food.id)] = {"score": item["score"], "breakdown": item["breakdown"]}
            stmt = pg_insert(FoodScore).values(
                user_id=user_id, food_id=food.id, score=item["score"],
                breakdown=item["breakdown"],
                model_version=engine_result["model_version"], computed_at=now,
            ).on_conflict_do_update(
                index_elements=[FoodScore.user_id, FoodScore.food_id],
                set_={"score": item["score"], "breakdown": item["breakdown"],
                      "model_version": engine_result["model_version"], "computed_at": now},
            )
            db.execute(stmt)
        db.commit()
    return result
```

- [ ] **Step 4: Implementar routes.py**

`services/core-api/src/core_api/scoring/routes.py`:

```python
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
```

Em `main.py`:

```python
from core_api.scoring.routes import router as scoring_router

app.include_router(scoring_router)
```

- [ ] **Step 5: Rodar, ver passar e commitar**

```bash
uv run pytest tests/test_scoring.py -v   # Expected: 4 PASSED
git add src/core_api/scoring src/core_api/main.py tests/test_scoring.py
git commit -m "feat(core-api): score público com cache TTL 24h e justificativa (SCRUM-18/19)"
```

---

### Task 9: Receitas — seeds e sugestão determinística (SCRUM-24)

**Files:**
- Create: `services/core-api/seeds/foods.json`
- Create: `services/core-api/seeds/recipes.json`
- Create: `services/core-api/src/core_api/seed.py`
- Create: `services/core-api/src/core_api/recipes/service.py`
- Create: `services/core-api/src/core_api/recipes/routes.py`
- Modify: `services/core-api/src/core_api/main.py`
- Test: `services/core-api/tests/test_recipes.py`, `services/core-api/tests/test_seed.py`

- [ ] **Step 1: Criar os seeds**

`services/core-api/seeds/foods.json` — alimentos básicos referenciados pelas receitas (chave `key` é só do seed, vira `name`):

```json
[
  {"key": "arroz_integral", "name": "Arroz integral", "food_group": "grain", "nutrition": {"energy_kcal_100g": 124, "proteins_100g": 2.6, "carbohydrates_100g": 25.8, "fat_100g": 1.0, "saturated_fat_100g": 0.3, "fiber_100g": 2.7, "sodium_mg_100g": 1, "sugar_100g": 0.4}, "allergen_flags": [], "flags": []},
  {"key": "feijao_preto", "name": "Feijão preto", "food_group": "legume", "nutrition": {"energy_kcal_100g": 77, "proteins_100g": 4.5, "carbohydrates_100g": 14, "fat_100g": 0.5, "saturated_fat_100g": 0.1, "fiber_100g": 8.4, "sodium_mg_100g": 2, "sugar_100g": 0.3}, "allergen_flags": [], "flags": []},
  {"key": "peito_frango", "name": "Peito de frango", "food_group": "meat", "nutrition": {"energy_kcal_100g": 165, "proteins_100g": 31, "carbohydrates_100g": 0, "fat_100g": 3.6, "saturated_fat_100g": 1.0, "fiber_100g": 0, "sodium_mg_100g": 74, "sugar_100g": 0}, "allergen_flags": [], "flags": ["animal_product", "meat"]},
  {"key": "ovo", "name": "Ovo", "food_group": "egg", "nutrition": {"energy_kcal_100g": 155, "proteins_100g": 13, "carbohydrates_100g": 1.1, "fat_100g": 11, "saturated_fat_100g": 3.3, "fiber_100g": 0, "sodium_mg_100g": 124, "sugar_100g": 1.1}, "allergen_flags": ["eggs"], "flags": ["animal_product"]},
  {"key": "aveia", "name": "Aveia em flocos", "food_group": "grain", "nutrition": {"energy_kcal_100g": 389, "proteins_100g": 16.9, "carbohydrates_100g": 66.3, "fat_100g": 6.9, "saturated_fat_100g": 1.2, "fiber_100g": 10.6, "sodium_mg_100g": 2, "sugar_100g": 0.99}, "allergen_flags": ["gluten"], "flags": []},
  {"key": "banana", "name": "Banana", "food_group": "fruit", "nutrition": {"energy_kcal_100g": 89, "proteins_100g": 1.1, "carbohydrates_100g": 22.8, "fat_100g": 0.3, "saturated_fat_100g": 0.1, "fiber_100g": 2.6, "sodium_mg_100g": 1, "sugar_100g": 12.2}, "allergen_flags": [], "flags": []},
  {"key": "maca", "name": "Maçã", "food_group": "fruit", "nutrition": {"energy_kcal_100g": 52, "proteins_100g": 0.3, "carbohydrates_100g": 14, "fat_100g": 0.2, "saturated_fat_100g": 0, "fiber_100g": 2.4, "sodium_mg_100g": 1, "sugar_100g": 10.4}, "allergen_flags": [], "flags": []},
  {"key": "brocolis", "name": "Brócolis", "food_group": "vegetable", "nutrition": {"energy_kcal_100g": 34, "proteins_100g": 2.8, "carbohydrates_100g": 6.6, "fat_100g": 0.4, "saturated_fat_100g": 0.1, "fiber_100g": 2.6, "sodium_mg_100g": 33, "sugar_100g": 1.7}, "allergen_flags": [], "flags": []},
  {"key": "tomate", "name": "Tomate", "food_group": "vegetable", "nutrition": {"energy_kcal_100g": 18, "proteins_100g": 0.9, "carbohydrates_100g": 3.9, "fat_100g": 0.2, "saturated_fat_100g": 0, "fiber_100g": 1.2, "sodium_mg_100g": 5, "sugar_100g": 2.6}, "allergen_flags": [], "flags": []},
  {"key": "batata_doce", "name": "Batata-doce", "food_group": "vegetable", "nutrition": {"energy_kcal_100g": 86, "proteins_100g": 1.6, "carbohydrates_100g": 20.1, "fat_100g": 0.1, "saturated_fat_100g": 0, "fiber_100g": 3, "sodium_mg_100g": 55, "sugar_100g": 4.2}, "allergen_flags": [], "flags": []},
  {"key": "iogurte_natural", "name": "Iogurte natural", "food_group": "dairy", "nutrition": {"energy_kcal_100g": 61, "proteins_100g": 3.3, "carbohydrates_100g": 4.7, "fat_100g": 3.3, "saturated_fat_100g": 1.9, "fiber_100g": 0, "sodium_mg_100g": 40, "sugar_100g": 4.7}, "allergen_flags": ["lactose"], "flags": ["animal_product"]},
  {"key": "queijo_minas", "name": "Queijo minas", "food_group": "dairy", "nutrition": {"energy_kcal_100g": 264, "proteins_100g": 17.4, "carbohydrates_100g": 3.2, "fat_100g": 20.2, "saturated_fat_100g": 12.4, "fiber_100g": 0, "sodium_mg_100g": 346, "sugar_100g": 3.2}, "allergen_flags": ["lactose"], "flags": ["animal_product"]},
  {"key": "tilapia", "name": "Filé de tilápia", "food_group": "fish", "nutrition": {"energy_kcal_100g": 96, "proteins_100g": 20.1, "carbohydrates_100g": 0, "fat_100g": 1.7, "saturated_fat_100g": 0.6, "fiber_100g": 0, "sodium_mg_100g": 52, "sugar_100g": 0}, "allergen_flags": [], "flags": ["animal_product", "fish"]},
  {"key": "lentilha", "name": "Lentilha", "food_group": "legume", "nutrition": {"energy_kcal_100g": 116, "proteins_100g": 9, "carbohydrates_100g": 20.1, "fat_100g": 0.4, "saturated_fat_100g": 0.1, "fiber_100g": 7.9, "sodium_mg_100g": 2, "sugar_100g": 1.8}, "allergen_flags": [], "flags": []},
  {"key": "grao_de_bico", "name": "Grão-de-bico", "food_group": "legume", "nutrition": {"energy_kcal_100g": 164, "proteins_100g": 8.9, "carbohydrates_100g": 27.4, "fat_100g": 2.6, "saturated_fat_100g": 0.3, "fiber_100g": 7.6, "sodium_mg_100g": 7, "sugar_100g": 4.8}, "allergen_flags": [], "flags": []},
  {"key": "azeite", "name": "Azeite de oliva", "food_group": "other", "nutrition": {"energy_kcal_100g": 884, "proteins_100g": 0, "carbohydrates_100g": 0, "fat_100g": 100, "saturated_fat_100g": 13.8, "fiber_100g": 0, "sodium_mg_100g": 2, "sugar_100g": 0}, "allergen_flags": [], "flags": []},
  {"key": "espinafre", "name": "Espinafre", "food_group": "vegetable", "nutrition": {"energy_kcal_100g": 23, "proteins_100g": 2.9, "carbohydrates_100g": 3.6, "fat_100g": 0.4, "saturated_fat_100g": 0.1, "fiber_100g": 2.2, "sodium_mg_100g": 79, "sugar_100g": 0.4}, "allergen_flags": [], "flags": []},
  {"key": "quinoa", "name": "Quinoa", "food_group": "grain", "nutrition": {"energy_kcal_100g": 120, "proteins_100g": 4.4, "carbohydrates_100g": 21.3, "fat_100g": 1.9, "saturated_fat_100g": 0.2, "fiber_100g": 2.8, "sodium_mg_100g": 7, "sugar_100g": 0.9}, "allergen_flags": [], "flags": []},
  {"key": "cenoura", "name": "Cenoura", "food_group": "vegetable", "nutrition": {"energy_kcal_100g": 41, "proteins_100g": 0.9, "carbohydrates_100g": 9.6, "fat_100g": 0.2, "saturated_fat_100g": 0, "fiber_100g": 2.8, "sodium_mg_100g": 69, "sugar_100g": 4.7}, "allergen_flags": [], "flags": []},
  {"key": "carne_moida", "name": "Carne moída magra", "food_group": "meat", "nutrition": {"energy_kcal_100g": 250, "proteins_100g": 26, "carbohydrates_100g": 0, "fat_100g": 15, "saturated_fat_100g": 6, "fiber_100g": 0, "sodium_mg_100g": 75, "sugar_100g": 0}, "allergen_flags": [], "flags": ["animal_product", "meat"]}
]
```

`services/core-api/seeds/recipes.json` — receitas referenciam alimentos pelo `key`:

```json
[
  {"name": "Arroz com feijão e frango grelhado", "ingredients": [{"food": "arroz_integral", "quantity": "1 xícara"}, {"food": "feijao_preto", "quantity": "1 concha"}, {"food": "peito_frango", "quantity": "150 g"}], "instructions": "Cozinhe o arroz e o feijão. Grelhe o frango temperado e sirva."},
  {"name": "Omelete de espinafre", "ingredients": [{"food": "ovo", "quantity": "2 unidades"}, {"food": "espinafre", "quantity": "1 punhado"}, {"food": "queijo_minas", "quantity": "30 g"}], "instructions": "Bata os ovos, misture o espinafre e o queijo, frite em fogo baixo."},
  {"name": "Mingau de aveia com banana", "ingredients": [{"food": "aveia", "quantity": "4 colheres"}, {"food": "banana", "quantity": "1 unidade"}], "instructions": "Cozinhe a aveia em água, fatie a banana por cima."},
  {"name": "Tilápia com legumes", "ingredients": [{"food": "tilapia", "quantity": "1 filé"}, {"food": "brocolis", "quantity": "1 xícara"}, {"food": "cenoura", "quantity": "1 unidade"}, {"food": "azeite", "quantity": "1 fio"}], "instructions": "Asse a tilápia com azeite; cozinhe os legumes no vapor."},
  {"name": "Salada de quinoa com grão-de-bico", "ingredients": [{"food": "quinoa", "quantity": "1 xícara"}, {"food": "grao_de_bico", "quantity": "meia xícara"}, {"food": "tomate", "quantity": "1 unidade"}, {"food": "azeite", "quantity": "1 fio"}], "instructions": "Misture tudo e tempere com azeite e limão."},
  {"name": "Sopa de lentilha", "ingredients": [{"food": "lentilha", "quantity": "1 xícara"}, {"food": "cenoura", "quantity": "1 unidade"}, {"food": "tomate", "quantity": "1 unidade"}], "instructions": "Cozinhe a lentilha com os legumes até ficar cremosa."},
  {"name": "Frango com batata-doce", "ingredients": [{"food": "peito_frango", "quantity": "150 g"}, {"food": "batata_doce", "quantity": "200 g"}, {"food": "brocolis", "quantity": "1 xícara"}], "instructions": "Asse a batata-doce, grelhe o frango e cozinhe o brócolis no vapor."},
  {"name": "Iogurte com frutas e aveia", "ingredients": [{"food": "iogurte_natural", "quantity": "1 pote"}, {"food": "banana", "quantity": "1 unidade"}, {"food": "maca", "quantity": "meia unidade"}, {"food": "aveia", "quantity": "2 colheres"}], "instructions": "Pique as frutas, misture com o iogurte e finalize com aveia."},
  {"name": "Bowl vegetariano", "ingredients": [{"food": "quinoa", "quantity": "1 xícara"}, {"food": "grao_de_bico", "quantity": "meia xícara"}, {"food": "espinafre", "quantity": "1 punhado"}, {"food": "tomate", "quantity": "1 unidade"}, {"food": "azeite", "quantity": "1 fio"}], "instructions": "Monte o bowl com a quinoa na base e os demais por cima."},
  {"name": "Ovos mexidos com tomate", "ingredients": [{"food": "ovo", "quantity": "2 unidades"}, {"food": "tomate", "quantity": "1 unidade"}], "instructions": "Refogue o tomate, junte os ovos e mexa até o ponto."},
  {"name": "Escondidinho de batata-doce com carne", "ingredients": [{"food": "batata_doce", "quantity": "300 g"}, {"food": "carne_moida", "quantity": "200 g"}, {"food": "queijo_minas", "quantity": "50 g"}], "instructions": "Faça o purê de batata-doce, cubra a carne refogada e gratine com queijo."},
  {"name": "Salada de feijão com ovo", "ingredients": [{"food": "feijao_preto", "quantity": "1 xícara"}, {"food": "ovo", "quantity": "1 unidade"}, {"food": "tomate", "quantity": "1 unidade"}, {"food": "azeite", "quantity": "1 fio"}], "instructions": "Misture o feijão frio com tomate picado e ovo cozido."},
  {"name": "Frango com quinoa e brócolis", "ingredients": [{"food": "peito_frango", "quantity": "150 g"}, {"food": "quinoa", "quantity": "1 xícara"}, {"food": "brocolis", "quantity": "1 xícara"}], "instructions": "Grelhe o frango e sirva sobre a quinoa com brócolis no vapor."},
  {"name": "Panqueca de banana e aveia", "ingredients": [{"food": "banana", "quantity": "1 unidade"}, {"food": "aveia", "quantity": "4 colheres"}, {"food": "ovo", "quantity": "1 unidade"}], "instructions": "Amasse a banana, misture com ovo e aveia, doure dos dois lados."},
  {"name": "Peixe com purê de cenoura", "ingredients": [{"food": "tilapia", "quantity": "1 filé"}, {"food": "cenoura", "quantity": "2 unidades"}, {"food": "azeite", "quantity": "1 fio"}], "instructions": "Cozinhe e amasse a cenoura; grelhe o peixe no azeite."},
  {"name": "Arroz integral com lentilha", "ingredients": [{"food": "arroz_integral", "quantity": "1 xícara"}, {"food": "lentilha", "quantity": "meia xícara"}, {"food": "cenoura", "quantity": "1 unidade"}], "instructions": "Cozinhe arroz e lentilha juntos com a cenoura em cubos."},
  {"name": "Salada completa de espinafre", "ingredients": [{"food": "espinafre", "quantity": "2 punhados"}, {"food": "queijo_minas", "quantity": "50 g"}, {"food": "tomate", "quantity": "1 unidade"}, {"food": "grao_de_bico", "quantity": "meia xícara"}], "instructions": "Misture as folhas com os demais ingredientes e tempere."},
  {"name": "Carne com legumes salteados", "ingredients": [{"food": "carne_moida", "quantity": "200 g"}, {"food": "brocolis", "quantity": "1 xícara"}, {"food": "cenoura", "quantity": "1 unidade"}], "instructions": "Refogue a carne e salteie os legumes na mesma panela."},
  {"name": "Vitamina de banana com aveia", "ingredients": [{"food": "banana", "quantity": "1 unidade"}, {"food": "iogurte_natural", "quantity": "1 pote"}, {"food": "aveia", "quantity": "2 colheres"}], "instructions": "Bata tudo no liquidificador."},
  {"name": "Maçã assada com canela", "ingredients": [{"food": "maca", "quantity": "2 unidades"}], "instructions": "Asse as maçãs com canela por 25 minutos."}
]
```

- [ ] **Step 2: Escrever teste do seed**

`services/core-api/tests/test_seed.py`:

```python
from core_api.db.models import Food, Recipe
from core_api.seed import run_seed


def test_seed_is_idempotent(db):
    run_seed(db)
    foods_count = db.query(Food).count()
    recipes_count = db.query(Recipe).count()
    assert foods_count == 20
    assert recipes_count == 20

    run_seed(db)  # segunda execução não duplica
    assert db.query(Food).count() == foods_count
    assert db.query(Recipe).count() == recipes_count


def test_seeded_recipe_has_ingredients(db):
    run_seed(db)
    recipe = db.query(Recipe).filter_by(name="Arroz com feijão e frango grelhado").one()
    assert len(recipe.ingredients) == 3
```

- [ ] **Step 3: Implementar seed.py**

`services/core-api/src/core_api/seed.py`:

```python
"""Seed de alimentos básicos e receitas pré-cadastradas (spec §5). Idempotente por nome."""
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from core_api.db.models import Food, Recipe, RecipeIngredient

SEEDS_DIR = Path(__file__).parents[2] / "seeds"


def run_seed(db: Session) -> None:
    foods_data = json.loads((SEEDS_DIR / "foods.json").read_text(encoding="utf-8"))
    recipes_data = json.loads((SEEDS_DIR / "recipes.json").read_text(encoding="utf-8"))

    foods_by_key: dict[str, Food] = {}
    for entry in foods_data:
        food = db.scalar(select(Food).where(Food.name == entry["name"]))
        if food is None:
            food = Food(name=entry["name"], food_group=entry["food_group"],
                        nutrition=entry["nutrition"],
                        allergen_flags=entry["allergen_flags"],
                        flags=entry["flags"], source="SEED")
            db.add(food)
            db.flush()
        foods_by_key[entry["key"]] = food

    for entry in recipes_data:
        if db.scalar(select(Recipe).where(Recipe.name == entry["name"])) is not None:
            continue
        recipe = Recipe(name=entry["name"], instructions=entry["instructions"],
                        nutrition_total={})
        db.add(recipe)
        db.flush()
        for ing in entry["ingredients"]:
            db.add(RecipeIngredient(recipe_id=recipe.id,
                                    food_id=foods_by_key[ing["food"]].id,
                                    quantity=ing["quantity"]))
    db.commit()


if __name__ == "__main__":
    from core_api.db.session import SessionLocal

    with SessionLocal() as session:
        run_seed(session)
        print("seed ok")
```

- [ ] **Step 4: Rodar testes do seed**

```bash
uv run pytest tests/test_seed.py -v
```

Expected: 2 PASSED.

- [ ] **Step 5: Escrever testes da sugestão de receitas**

`services/core-api/tests/test_recipes.py`:

```python
import respx
from httpx import Response

from core_api.db.models import Food
from core_api.seed import run_seed
from core_api.settings import settings

from tests.helpers import auth_headers
from tests.test_profile import PROFILE

ENGINE_URL = f"{settings.score_engine_url}/score"


def _engine_ok(request):
    """Mock dinâmico: score 0.9 para qualquer alimento pedido."""
    import json
    payload = json.loads(request.content)
    scores = [{"food_id": f["food_id"], "score": 0.9,
               "breakdown": {"allergen_safe": True, "diet_compatible": True,
                             "goal_alignment": "high", "health_flags": [],
                             "heuristic_reference": 9.0}}
              for f in payload["foods"]]
    return Response(200, json={"scores": scores, "model_version": "mlp-v1", "engine": "mlp"})


def _setup(client, db):
    run_seed(db)
    headers, user_id = auth_headers(client)
    client.put(f"/perfil/{user_id}", json=PROFILE, headers=headers)

    # Dispensa: banana + aveia + iogurte → cobre 100% de "Vitamina de banana com aveia"
    # e 100% de "Mingau de aveia com banana"
    for name in ["Banana", "Aveia em flocos", "Iogurte natural"]:
        food = db.query(Food).filter_by(name=name).one()
        client.post(f"/dispensa/{user_id}/adicionar", headers=headers,
                    json={"alimento_id": str(food.id)})
    return headers, user_id


@respx.mock
def test_suggestions_only_include_covered_recipes(client, db):
    respx.post(ENGINE_URL).mock(side_effect=_engine_ok)
    headers, user_id = _setup(client, db)

    resp = client.get(f"/receitas/sugeridas/{user_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["scored"] is True
    names = [r["name"] for r in body["receitas"]]
    assert "Vitamina de banana com aveia" in names
    assert "Mingau de aveia com banana" in names
    assert "Tilápia com legumes" not in names  # cobertura 0%
    for r in body["receitas"]:
        assert r["coverage"] >= 0.7


@respx.mock
def test_suggestions_are_deterministic(client, db):
    respx.post(ENGINE_URL).mock(side_effect=_engine_ok)
    headers, user_id = _setup(client, db)
    first = client.get(f"/receitas/sugeridas/{user_id}", headers=headers).json()
    second = client.get(f"/receitas/sugeridas/{user_id}", headers=headers).json()
    assert first == second


@respx.mock
def test_engine_down_degrades_to_coverage_order(client, db):
    respx.post(ENGINE_URL).mock(side_effect=Exception("down"))
    headers, user_id = _setup(client, db)

    resp = client.get(f"/receitas/sugeridas/{user_id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["scored"] is False
    assert all(r["score_medio"] is None for r in body["receitas"])
    assert len(body["receitas"]) >= 1


def test_empty_pantry_returns_empty_list(client, db):
    run_seed(db)
    headers, user_id = auth_headers(client)
    client.put(f"/perfil/{user_id}", json=PROFILE, headers=headers)
    body = client.get(f"/receitas/sugeridas/{user_id}", headers=headers).json()
    assert body["receitas"] == []
```

- [ ] **Step 6: Rodar e ver falhar**

```bash
uv run pytest tests/test_recipes.py -v
```

Expected: FAIL — 404 na rota.

- [ ] **Step 7: Implementar service.py e routes.py**

`services/core-api/src/core_api/recipes/service.py`:

```python
"""
Sugestão determinística de receitas (SCRUM-24, spec §5).

Regras: cobertura de ingredientes na dispensa >= 70%; ordenação por
(score médio desc, cobertura desc, nome asc) — ordem total estável.
Engine indisponível → degrada para (cobertura desc, nome asc) com scored=False.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core_api.db.models import Food, PantryItem, Profile, Recipe
from core_api.scoring.engine_client import EngineUnavailableError
from core_api.scoring.service import get_scores

COVERAGE_THRESHOLD = 0.7


def suggest_recipes(db: Session, profile: Profile, limit: int = 10) -> dict:
    pantry_food_ids = set(db.scalars(
        select(PantryItem.food_id).where(PantryItem.user_id == profile.user_id)
    ).all())
    if not pantry_food_ids:
        return {"receitas": [], "scored": False}

    recipes = db.scalars(
        select(Recipe).options(selectinload(Recipe.ingredients))
    ).all()

    candidates = []
    for recipe in recipes:
        ingredient_ids = [ing.food_id for ing in recipe.ingredients]
        if not ingredient_ids:
            continue
        present = [fid for fid in ingredient_ids if fid in pantry_food_ids]
        coverage = len(present) / len(ingredient_ids)
        if coverage >= COVERAGE_THRESHOLD:
            candidates.append((recipe, present, ingredient_ids, coverage))

    if not candidates:
        return {"receitas": [], "scored": False}

    # Scores dos alimentos da dispensa usados pelos candidatos (cache → engine)
    scored = True
    needed_ids = {fid for _, present, _, _ in candidates for fid in present}
    foods = db.scalars(select(Food).where(Food.id.in_(needed_ids))).all()
    try:
        scores = get_scores(db, profile, foods)
    except EngineUnavailableError:
        scored = False
        scores = {}

    results = []
    for recipe, present, ingredient_ids, coverage in candidates:
        if scored and present:
            avg = round(sum(scores[str(fid)]["score"] for fid in present) / len(present), 3)
        else:
            avg = None
        missing = [str(fid) for fid in ingredient_ids if fid not in pantry_food_ids]
        results.append({
            "id": str(recipe.id), "name": recipe.name,
            "instructions": recipe.instructions,
            "coverage": round(coverage, 3), "score_medio": avg,
            "ingredientes_faltantes": sorted(missing),
        })

    if scored:
        results.sort(key=lambda r: (-r["score_medio"], -r["coverage"], r["name"]))
    else:
        results.sort(key=lambda r: (-r["coverage"], r["name"]))
    return {"receitas": results[:limit], "scored": scored}
```

`services/core-api/src/core_api/recipes/routes.py`:

```python
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
```

Em `main.py`:

```python
from core_api.recipes.routes import router as recipes_router

app.include_router(recipes_router)
```

- [ ] **Step 8: Rodar tudo, ver passar e commitar**

```bash
uv run pytest -v && uv run ruff check .
```

Expected: suíte completa PASSED, lint limpo.

```bash
git add seeds/ src/core_api/seed.py src/core_api/recipes src/core_api/main.py tests/
git commit -m "feat(core-api): seeds e sugestão determinística de receitas (SCRUM-24)"
```

---

### Task 10: Docker, compose e CI

**Files:**
- Create: `services/core-api/Dockerfile`, `services/core-api/.dockerignore`
- Modify: `docker-compose.yml` (raiz)
- Modify: `.github/workflows/ci.yml`
- Modify: `.env.example`

- [ ] **Step 1: Dockerfile e .dockerignore**

`services/core-api/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini ./
COPY seeds/ seeds/

EXPOSE 8000
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && \
     uv run --no-sync python -m core_api.seed && \
     uv run --no-sync uvicorn core_api.main:app --host 0.0.0.0 --port 8000"]
```

`services/core-api/.dockerignore`:

```
.venv/
tests/
__pycache__/
.pytest_cache/
.ruff_cache/
```

- [ ] **Step 2: Adicionar core-api ao docker-compose.yml**

Adicionar ao bloco `services:` do `docker-compose.yml` da raiz:

```yaml
  core-api:
    build: services/core-api
    environment:
      CORE_DATABASE_URL: postgresql+psycopg://${POSTGRES_USER:-helfy}:${POSTGRES_PASSWORD:-helfy}@postgres:5432/${POSTGRES_DB:-helfy}
      CORE_SCORE_ENGINE_URL: http://score-engine:8001
      CORE_JWT_SECRET: ${CORE_JWT_SECRET:-dev-secret-change-me}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      score-engine:
        condition: service_healthy
```

E em `.env.example`, acrescentar:

```bash
CORE_JWT_SECRET=dev-secret-change-me
```

- [ ] **Step 3: Adicionar job da core-api ao CI**

Em `.github/workflows/ci.yml`, acrescentar ao bloco `jobs:`:

```yaml
  core-api:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/core-api
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: helfy
          POSTGRES_PASSWORD: helfy
          POSTGRES_DB: helfy_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U helfy"
          --health-interval 5s --health-timeout 3s --health-retries 10
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Instalar dependências
        run: uv sync
      - name: Lint
        run: uv run ruff check .
      - name: Testes
        run: uv run pytest -v
```

- [ ] **Step 4: Smoke test do stack completo**

```bash
cd /home/bcr/estudos/helfy
docker compose up --build -d
sleep 15
curl -s localhost:8000/health
curl -s -X POST localhost:8000/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"smoke@helfy.app","password":"s3nh4-forte","name":"Smoke"}'
TOKEN=$(curl -s -X POST localhost:8000/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"smoke@helfy.app","password":"s3nh4-forte"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s localhost:8000/docs -o /dev/null -w "docs: %{http_code}\n"
echo "token ok: ${TOKEN:0:20}..."
docker compose down
```

Expected: health ok, registro 201, token JWT emitido, /docs 200.

- [ ] **Step 5: Commitar**

```bash
git add services/core-api/Dockerfile services/core-api/.dockerignore \
        docker-compose.yml .env.example .github/workflows/ci.yml services/core-api/uv.lock
git commit -m "feat(core-api): docker, compose com stack completo e job de CI"
```

---

### Task 11: README do serviço e verificação final

**Files:**
- Create: `services/core-api/README.md`
- Modify: `README.md` (raiz)

- [ ] **Step 1: README do serviço**

`services/core-api/README.md`:

```markdown
# core-api

API de produto do Helfy: autenticação JWT, perfil de saúde, base de alimentos
(Open Food Facts + input manual), dispensa digital, score nutricional
personalizado (consome a score-engine, cache TTL 24h) e sugestão determinística
de receitas.

## Rodar

```bash
docker compose up -d postgres          # na raiz do monorepo
uv sync
uv run alembic upgrade head
uv run python -m core_api.seed         # alimentos básicos + receitas
uv run uvicorn core_api.main:app --port 8000 --reload
# Swagger: http://localhost:8000/docs
```

## Testes

```bash
docker compose up -d postgres
docker compose exec postgres createdb -U helfy helfy_test || true
uv run pytest -v && uv run ruff check .
```

## Domínios

| Módulo | Rotas | SCRUM |
|---|---|---|
| auth | POST /auth/register, /auth/login, GET /auth/me | 12 |
| profile | GET/PUT /perfil/{id} | 13 |
| foods | GET /alimentos/barcode/{codigo}, GET /alimentos/{id}, POST /alimentos | 14/15/16 |
| pantry | GET/POST/DELETE /dispensa/... | 21 |
| scoring | POST /score (cache food_scores, TTL 24h) | 18/19 |
| recipes | GET /receitas/sugeridas/{usuario_id} | 24 |
```

- [ ] **Step 2: Atualizar README da raiz**

Na tabela de estrutura do `README.md` da raiz, remover o sufixo "— Plano 2" da linha da core-api e acrescentar abaixo do bloco de `docker compose up`:

```markdown
# core-api:      http://localhost:8000/docs
```

- [ ] **Step 3: Verificação final e commit**

```bash
cd services/core-api && uv run pytest -v && uv run ruff check . && cd ../..
git add services/core-api/README.md README.md
git commit -m "docs(core-api): documentação do serviço e atualização do README raiz"
```

Expected: suíte completa PASSED antes do commit.

---

## Critérios de aceite do plano (verificação final)

- [ ] `docker compose up --build` sobe postgres + score-engine + core-api; migrations e seed rodam no boot
- [ ] Fluxo completo via Swagger: register → login → PUT perfil → adicionar à dispensa (barcode ou manual) → POST /score (0–1 + justificativa) → GET /receitas/sugeridas determinístico
- [ ] Cache de scores: TTL 24h + invalidação no PUT /perfil (testes cobrem ambos)
- [ ] Engine fora do ar: /score → 503; /receitas/sugeridas → degrada por cobertura com `scored: false`
- [ ] Usuário não acessa recurso de outro (403 testado em perfil e dispensa)
- [ ] `/docs`, `/redoc` e `/openapi.json` servidos (spec §7); CI verde nos dois serviços
- [ ] Nenhum commit com trailer de IA
