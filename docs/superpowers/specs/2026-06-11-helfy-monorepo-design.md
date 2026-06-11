# Helfy — Design do Monorepo (Sprint 1)

**Data:** 2026-06-11
**Status:** Aprovado
**Contexto:** FIAP Challenge / CarePlus. App mobile de alimentação saudável personalizada por IA. Este documento é a spec de arquitetura do monorepo cobrindo todas as tasks da Sprint 1 (SCRUM-12 a SCRUM-29).

## 1. Decisões fundamentais

| Decisão | Escolha | Justificativa |
|---|---|---|
| Stack de backend | Python/FastAPI (todos os serviços) | Um ecossistema só; reaproveita padrões da engine existente; velocidade de desenvolvimento para o challenge |
| Engine de score | Replicar de `~/estudos/checkpoints/chall-ia` e adaptar | Modelo MLP treinado (R²=0.97) e pipeline já validados; adapta-se o contrato, não o modelo |
| Granularidade | 2 serviços: `core-api` + `score-engine` | Engine isolada (princípio do projeto); demais domínios modularizados dentro da core-api, fatiáveis depois |
| Banco | PostgreSQL (Alembic + SQLAlchemy 2) | Padrão de mercado, JSONB para info nutricional, sobe em docker-compose |
| Mobile | Expo + TypeScript | Setup rápido, expo-camera para barcode, ideal para o prazo |
| Auth | JWT (python-jose + bcrypt) | Conforme convenção do projeto |
| Documentação de API | Swagger/OpenAPI gerada automaticamente em toda API | FastAPI gera nativamente; exigência do projeto |
| Idioma | Código em inglês; commits/comentários em português | Convenção do projeto |

## 2. Arquitetura

```
mobile (Expo/RN)
   │  HTTPS + JWT
   ▼
core-api (FastAPI + PostgreSQL)           score-engine (FastAPI + MLP)
   ├─ auth/profile   (SCRUM-7)               │  STATELESS — sem banco
   ├─ foods          (SCRUM-14/15/16)  HTTP  │  recebe perfil + alimentos
   ├─ pantry         (SCRUM-10)      ───────►│  no request; devolve scores
   └─ recipes        (SCRUM-11)              │  0–1 + breakdown (SCRUM-19)
```

**A engine é stateless.** O chall-ia original guarda indivíduos em memória (`_individuals: dict` em `src/api/main.py:46`) — isso é removido. A core-api é a única dona de dados; ao pedir score, envia o perfil completo do usuário e a info nutricional dos alimentos no corpo da requisição. Benefícios: elimina a maior dívida técnica do chall-ia (estado efêmero), mantém a IA substituível sem impacto no produto, dispensa sincronização de dados entre serviços.

O contrato público `POST /score { usuario_id, alimento_ids[] }` (CLAUDE.md §6) vive na **core-api**, que resolve usuário/alimentos no banco e chama a engine. O score do modelo (0–10) é normalizado para **0.0–1.0** na resposta da engine.

## 3. Estrutura do monorepo

```
helfy/
├─ apps/
│  └─ mobile/                  # Expo + TypeScript
│     ├─ app/                  # expo-router: (auth)/, (tabs)/, onboarding/
│     ├─ src/{api,components,hooks,store}/
│     └─ package.json
├─ services/
│  ├─ core-api/
│  │  ├─ src/core_api/
│  │  │  ├─ auth/              # registro, login, JWT
│  │  │  ├─ profile/           # perfil de saúde
│  │  │  ├─ foods/             # base de produtos + Open Food Facts
│  │  │  ├─ pantry/            # dispensa digital
│  │  │  ├─ recipes/           # receitas + sugestão determinística
│  │  │  ├─ scoring/           # cliente HTTP da engine + cache de scores
│  │  │  ├─ db/                # engine SQLAlchemy, session, base
│  │  │  └─ main.py
│  │  ├─ alembic/
│  │  ├─ seeds/                # receitas pré-cadastradas (JSON)
│  │  ├─ tests/
│  │  └─ pyproject.toml        # uv
│  └─ score-engine/
│     ├─ src/score_engine/
│     │  ├─ api/               # FastAPI: /score, /health
│     │  ├─ mapping/           # perfil Helfy → features do modelo
│     │  ├─ features/          # preprocessing (replicado)
│     │  ├─ model/             # train/evaluate (replicado, p/ retreino)
│     │  ├─ data/              # pipeline de dados (replicado)
│     │  └─ scoring.py         # heurística (replicada) — fallback e ground truth
│     ├─ artifacts/            # mlp_model.pkl, preprocessor.pkl (versionados)
│     ├─ tests/
│     └─ pyproject.toml
├─ docs/
│  ├─ approach.md              # migrado do chall-ia, atualizado
│  └─ superpowers/specs/
├─ docker-compose.yml          # postgres + core-api + score-engine
├─ .github/workflows/ci.yml    # pytest + ruff nos 2 serviços
├─ CLAUDE.md                   # contexto canônico do projeto (fornecido)
└─ README.md
```

Cada serviço Python tem `pyproject.toml` próprio e Dockerfile próprio. Sem ferramenta de monorepo (nx/turbo) — docker-compose é a costura. Artefatos `.pkl` são versionados no git (≈600 KB total, aceitável; se crescerem, migrar para Git LFS).

## 4. score-engine: replicação e adaptações

### Replica sem mudança funcional
- Modelo treinado (`mlp_model.pkl`) e preprocessador (`preprocessor.pkl`)
- Pipeline de features (`preprocessing.py` — ColumnTransformer: StandardScaler + OneHotEncoder)
- Pipeline de dados e treino (`fetch_foods`, `generate_individuals`, `generate_pairs`, `train`, `evaluate`) — mantidos para retreinos futuros
- Heurística `compute_score` — vira fallback explícito e ground truth dos testes
- Breakdown de explicabilidade (allergen_safe, diet_compatible, goal_alignment, health_flags)

### Adaptações (o "aprimorar")
1. **Novo contrato stateless** — remove `/individuals` e o estado em memória:
   ```
   POST /score
   { "profile": { goal, diet_type, activity_level, age, weight_kg, height_cm,
                  total_cholesterol, glucose, allergies[], restrictions[] },
     "foods": [ { food_id, food_group, nutrition{...}, allergen_flags[] } ] }
   →
   { "scores": [ { food_id, score: 0.0–1.0, breakdown{...} } ],
     "model_version": "mlp-v1" }
   ```
2. **Camada de mapeamento de domínio** (`mapping/`): traduz o perfil Helfy para as features do modelo:
   - `objetivo` EMAGRECER/GANHAR_MASSA/MANTER → `goal` weight_loss/muscle_gain/maintenance
   - `glicose` (mg/dL) → `glycemic_condition` (none / pre_diabetic / type_2, por faixas clínicas: <100 none, 100–125 pre_diabetic, ≥126 type_2)
   - `restricoes` "lactose"/"gluten"/"vegano" etc. → flags de alergia e `diet_type`
   - Campos coletados no onboarding que o modelo usa diretamente: `diet_type`, `activity_level`, alergias
   - Defaults documentados para campos ausentes (ex.: `hypertension=none` enquanto o perfil não coletar pressão)
3. **Qualidade**: pytest (heurística com casos conhecidos: alérgeno → 0, vegano+carne penalizado, hipertenso+sódio penalizado; shape do preprocessing; contrato via TestClient; sanidade do modelo: vetor fixo → score dentro de tolerância), Dockerfile, logging estruturado (stdlib `logging` + JSON), validação dos artefatos no startup com `/health` informando `model_loaded`.
4. **Fallback**: se o modelo não carregar, a engine responde com a heurística e marca `"engine": "heuristic"` na resposta — nunca silenciosamente.

## 5. core-api: domínios e modelo de banco (SCRUM-20)

### Schema (PostgreSQL, migrations Alembic)

```
users            (id uuid pk, email unique, password_hash, name, created_at)
profiles         (user_id pk/fk, height_cm, weight_kg, goal enum, diet_type enum,
                  activity_level enum, cholesterol int?, glucose int?,
                  restrictions text[], preferences text[], allergies text[],
                  updated_at)
foods            (id uuid pk, barcode unique?, name, food_group,
                  nutrition jsonb,            -- calorias, proteínas, carbs, gorduras, fibras, sódio, açúcar /100g
                  allergen_flags text[], source enum(OFF, MANUAL), created_at)
pantry_items     (user_id fk, food_id fk, quantity numeric?, added_at,
                  pk(user_id, food_id))
recipes          (id uuid pk, name, instructions text, nutrition_total jsonb)
recipe_ingredients (recipe_id fk, food_id fk, quantity?, pk(recipe_id, food_id))
food_scores      (user_id fk, food_id fk, score numeric(4,3), breakdown jsonb,
                  model_version, computed_at, pk(user_id, food_id))   -- cache
```

Invalidação do cache `food_scores`:
- **Por evento:** deletar as linhas do usuário quando o perfil é atualizado (`PUT /perfil`)
- **Por TTL: 24h** — entradas com `computed_at` mais antigo que 24 horas são tratadas como miss e recalculadas na engine (verificação na leitura; sem job de limpeza na Sprint 1)

### Base de produtos (SCRUM-14)
Open Food Facts como fonte. `GET /alimentos/barcode/{codigo}`: busca local primeiro; em miss, consulta a API do OFF, normaliza os campos nutricionais para o formato `nutrition` e os `allergen_flags`/`food_group` usados pela engine, e persiste. Input manual (SCRUM-15) cria `foods` com `source=MANUAL` sem barcode. Timeout/erro do OFF → 502 com mensagem clara; nunca bloqueia o input manual.

### Receitas sugeridas (SCRUM-24 — determinístico)
`GET /receitas/sugeridas/{usuario_id}`:
1. Carrega dispensa do usuário
2. Obtém scores dos alimentos da dispensa (cache `food_scores`; misses vão em lote à engine)
3. Seleciona receitas com cobertura de ingredientes na dispensa ≥ 70%
4. Ordena por média dos scores dos ingredientes presentes (desempate: maior cobertura, depois nome — ordem total estável)
5. Retorna top N com score médio, ingredientes faltantes e breakdown

Sem aleatoriedade em nenhum passo: mesmo input ⇒ mesmo output. Se a engine estiver indisponível, ordena só por cobertura e marca `"scored": false` na resposta (degradação explícita, ainda determinística). Receitas pré-cadastradas: seed JSON com 20–30 receitas referenciando alimentos também seedados.

### Endpoints públicos
Conforme CLAUDE.md §6: `POST /auth/register`, `POST /auth/login`, `GET/PUT /perfil/{id}`, `GET/POST/DELETE /dispensa/...`, `POST /score`, `GET /receitas/sugeridas/{usuario_id}`, `GET /alimentos/barcode/{codigo}`, `GET /alimentos/{id}`. Todas exceto auth exigem `Authorization: Bearer <token>`; um usuário só acessa os próprios recursos (403 caso contrário).

## 6. Mobile (Expo)

- **Navegação:** expo-router — grupos `(auth)` (login/registro), `onboarding/` (wizard de perfil), `(tabs)` (home/receitas, dispensa, perfil)
- **Telas Sprint 1:** cadastro/login (SCRUM-12), onboarding wizard (SCRUM-27: dados básicos → objetivo → dieta/restrições/alergias → marcadores de saúde), perfil (SCRUM-28), cadastro de produto com scan via expo-camera + formulário manual (SCRUM-29), dispensa (SCRUM-26), home com receitas sugeridas exibindo score e justificativa (SCRUM-19 no front)
- **Dados:** React Query para chamadas/cache; JWT em expo-secure-store; cliente API tipado em `src/api/`
- **Score no cliente:** nunca calculado — apenas exibido (convenção do projeto)

## 7. Documentação de API (Swagger/OpenAPI)

Toda API do monorepo expõe documentação Swagger/OpenAPI **gerada automaticamente** pelo FastAPI:

- `core-api` e `score-engine` servem Swagger UI em `/docs`, ReDoc em `/redoc` e o schema em `/openapi.json`
- Os modelos Pydantic de request/response levam `description` e `examples` (via `model_config["json_schema_extra"]` ou `Field(examples=...)`) para que o schema gerado seja autoexplicativo — incluindo um exemplo completo de perfil e de resposta de score com breakdown
- Cada endpoint declara `summary`, `tags` por domínio (auth, profile, foods, pantry, recipes, score) e `response_model` explícito — nada de retornar dicts soltos, senão o schema gerado fica vazio
- O CI valida que `/openapi.json` é gerado sem erros (teste de smoke via TestClient)

## 8. Testes e CI

- **score-engine:** unit (heurística, mapping, preprocessing) + integração (TestClient, modelo real carregado)
- **core-api:** unit (regras de sugestão, normalização OFF, invalidação de cache) + integração (TestClient + Postgres via testcontainers ou compose no CI; engine mockada com respx)
- **mobile:** smoke de renderização das telas principais (jest-expo); E2E fora do escopo da Sprint 1
- **CI (GitHub Actions):** jobs paralelos por serviço — ruff + pytest; tsc + jest no mobile

## 9. Fases de execução

| Fase | Conteúdo | Tasks SCRUM |
|---|---|---|
| 1. Fundação | Scaffold do monorepo, docker-compose, CI, migrations base | SCRUM-23, SCRUM-20 |
| 2. Engine | Replicar chall-ia, contrato stateless, mapping, testes, Docker | SCRUM-17, 18, 19 |
| 3a. Core: auth+perfil | Registro, login, perfil CRUD | SCRUM-12, 13 |
| 3b. Core: alimentos+dispensa | OFF, input manual, API da dispensa | SCRUM-14, 15, 16, 21 |
| 4. Receitas | Seed + serviço determinístico + integração engine | SCRUM-24 |
| 5. Mobile | Todas as telas sobre as APIs prontas | SCRUM-26, 27, 28, 29 |

Fases 3a e 3b são paralelizáveis. A fase 5 pode começar pelo setup de navegação/auth assim que a 3a expõe os endpoints.

## 10. Fora de escopo (Sprint 1)

Notificações, plano semanal, lista de compras, marketplace, telemetria CarePlus (roadmap pós-MVP); retreino automático do modelo; observabilidade além de logging; deploy em nuvem (somente docker-compose local).
