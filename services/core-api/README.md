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
