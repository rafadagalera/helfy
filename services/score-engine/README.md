# score-engine

Engine de score nutricional do Helfy. Serviço FastAPI **stateless**: recebe o perfil
do usuário (vocabulário Helfy) + alimentos no request e devolve scores 0.0–1.0 com
breakdown de explicabilidade. Modelo MLP treinado replicado do projeto chall-ia
(ver `docs/approach.md` na raiz do monorepo).

## Rodar

```bash
uv sync
uv run uvicorn score_engine.api.main:app --port 8001 --reload
# Swagger: http://localhost:8001/docs
```

## Testes

```bash
uv run pytest -v && uv run ruff check .
```

## Retreino do modelo (manual, fora do escopo da Sprint 1)

Os módulos `score_engine/data/` e `score_engine/model/` são o pipeline original de
treino (Open Food Facts → indivíduos sintéticos → pares com heurística → MLP).
Eles esperam um diretório `data/` na raiz do serviço (ignorado pelo git) e foram
mantidos como vieram do chall-ia. Para retreinar: replicar os 5 passos do
`run_pipeline.py` do projeto original e copiar os novos `.pkl` para `artifacts/`,
atualizando `MODEL_VERSION` em `src/score_engine/service.py`.

## Contrato

`POST /score` — ver exemplos no Swagger (`/docs`). Resposta inclui `engine: "mlp" |
"heuristic"` — `heuristic` significa que os artefatos não carregaram (fallback).
