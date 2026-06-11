# Plano 1 — Fundação do Monorepo + score-engine

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Montar a fundação do monorepo Helfy (scaffold, docker-compose, CI) e entregar o serviço `score-engine` funcionando: código replicado de `~/estudos/checkpoints/chall-ia`, adaptado para contrato stateless com score 0–1, testado e dockerizado.

**Architecture:** O `score-engine` é um serviço FastAPI stateless: recebe perfil Helfy + alimentos no request, traduz para as features do modelo MLP treinado (camada `mapping/`), roda o preprocessador + modelo replicados do chall-ia e devolve scores 0.0–1.0 com breakdown de explicabilidade. Se o modelo não carregar, cai na heurística original com `engine: "heuristic"` explícito.

**Tech Stack:** Python 3.12, uv, FastAPI, Pydantic v2, scikit-learn (MLP já treinado — `.pkl` replicado), pandas, pytest, ruff, Docker/docker-compose, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-06-11-helfy-monorepo-design.md` (seções 2–4, 7–9)

**Planos seguintes (não cobertos aqui):** Plano 2 = core-api (fases 3–4 da spec); Plano 3 = mobile (fase 5).

**Convenções:** código em inglês; commits em português; NUNCA incluir trailers de IA/Co-Authored-By nos commits.

---

## Contexto para quem nunca viu o projeto

- O código-fonte original a replicar está em `/home/bcr/estudos/checkpoints/chall-ia/` (fora deste repo). Os artefatos do modelo (`mlp_model.pkl`, `preprocessor.pkl`) estão em `chall-ia/data/models/`.
- O modelo prevê um score **0–10** para um par indivíduo × alimento, a partir de 36 colunas brutas (definidas em `chall-ia/src/features/preprocessing.py`: `IND_NUM`, `IND_CAT`, `IND_BIN`, `FOOD_NUM`, `FOOD_CAT`, `FOOD_BIN`).
- A heurística `compute_score(ind: pd.Series, food: pd.Series, noise_std=0.0) -> float` (em `chall-ia/src/data/generate_pairs.py`) é o ground truth do modelo e o fallback em runtime.
- O contrato público do Helfy usa score **0.0–1.0** — a normalização (÷10) acontece neste serviço.
- Rodar comandos Python sempre via `uv run ...` dentro de `services/score-engine/`.

---

### Task 1: Scaffold do monorepo

**Files:**
- Create: `.gitignore`, `README.md`
- Create (dirs): `apps/`, `services/`, `docs/superpowers/plans/`

- [ ] **Step 1: Criar .gitignore na raiz**

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
*.egg-info/
.pytest_cache/
.ruff_cache/

# Node / Expo
node_modules/
.expo/
dist/

# Ambiente
.env
.env.*
!.env.example

# Dados gerados em runtime (artefatos do modelo em artifacts/ SÃO versionados)
services/score-engine/data/raw/
services/score-engine/data/processed/

# IDE
.idea/
.vscode/
```

- [ ] **Step 2: Criar README.md na raiz**

```markdown
# Helfy

App mobile de alimentação saudável personalizada por IA — FIAP Challenge / CarePlus.

## Estrutura

| Caminho | O que é |
|---|---|
| `apps/mobile/` | App React Native (Expo) — Plano 3 |
| `services/core-api/` | API de produto: auth, perfil, alimentos, dispensa, receitas — Plano 2 |
| `services/score-engine/` | Engine de score nutricional (ML, stateless) |
| `docs/` | Specs, planos e documentação técnica |

## Rodando localmente

```bash
docker compose up --build
# score-engine: http://localhost:8001/docs
# postgres:     localhost:5432 (helfy/helfy)
```

## Documentação

- Arquitetura: `docs/superpowers/specs/2026-06-11-helfy-monorepo-design.md`
- Contexto canônico: `CLAUDE.md`
```

- [ ] **Step 3: Criar diretórios e commitar**

```bash
mkdir -p apps services docs/superpowers/plans
git add .gitignore README.md
git commit -m "chore: scaffold inicial do monorepo"
```

---

### Task 2: score-engine — pacote Python e código replicado do chall-ia

**Files:**
- Create: `services/score-engine/pyproject.toml`
- Create: `services/score-engine/src/score_engine/__init__.py` (e `__init__.py` em cada subpacote)
- Copy: `chall-ia/src/features/preprocessing.py` → `services/score-engine/src/score_engine/features/preprocessing.py`
- Copy: `chall-ia/src/data/*.py` → `services/score-engine/src/score_engine/data/`
- Copy: `chall-ia/src/model/*.py` → `services/score-engine/src/score_engine/model/`
- Copy: `chall-ia/data/models/{mlp_model,preprocessor}.pkl` → `services/score-engine/artifacts/`
- Test: `services/score-engine/tests/test_artifacts.py`

- [ ] **Step 1: Criar estrutura e pyproject.toml**

```bash
mkdir -p services/score-engine/src/score_engine/{api,mapping,features,model,data} \
         services/score-engine/{artifacts,tests}
```

Conteúdo de `services/score-engine/pyproject.toml`:

```toml
[project]
name = "score-engine"
version = "1.0.0"
description = "Helfy — engine de score nutricional (par usuário × alimento)"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111",
    "uvicorn[standard]>=0.29",
    "scikit-learn>=1.4,<1.6",
    "pandas>=2.0",
    "numpy>=1.26",
    "joblib>=1.4",
    "pydantic>=2.7",
    "requests>=2.31",
    "matplotlib>=3.8",
    "seaborn>=0.13",
]

[dependency-groups]
dev = ["pytest>=8", "httpx>=0.27", "ruff>=0.4"]

[tool.pytest.ini_options]
# "." no pythonpath permite que testes importem fixtures uns dos outros (from tests.test_mapping import ...)
pythonpath = ["src", "."]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
src = ["src", "tests"]
```

Nota: `scikit-learn` com teto `<1.6` porque os `.pkl` foram serializados nessa família de versão — unpickle entre versões muito diferentes pode falhar (o teste do Step 4 valida).

- [ ] **Step 2: Copiar código e artefatos do chall-ia**

```bash
CHALL=/home/bcr/estudos/checkpoints/chall-ia
ENG=services/score-engine

cp $CHALL/src/features/preprocessing.py $ENG/src/score_engine/features/
cp $CHALL/src/data/fetch_foods.py $CHALL/src/data/generate_individuals.py \
   $CHALL/src/data/generate_pairs.py $CHALL/src/data/mock_foods.py \
   $ENG/src/score_engine/data/
cp $CHALL/src/model/train.py $CHALL/src/model/evaluate.py $ENG/src/score_engine/model/
cp $CHALL/data/models/mlp_model.pkl $CHALL/data/models/preprocessor.pkl $ENG/artifacts/

touch $ENG/src/score_engine/__init__.py \
      $ENG/src/score_engine/{api,mapping,features,model,data}/__init__.py
```

- [ ] **Step 3: Ajustar imports dos módulos copiados**

Os arquivos copiados importam `from src....` (layout antigo). Reescrever para o pacote novo:

```bash
cd services/score-engine
grep -rl "from src\." src/ | xargs sed -i 's/from src\./from score_engine./g'
grep -rl "import src\." src/ | xargs sed -i 's/import src\./import score_engine./g'
grep -rn "src\." src/score_engine/ | grep -v score_engine  # conferir que não sobrou nada
```

Os scripts de pipeline (`data/`, `model/`) referenciam caminhos `data/raw|processed|models` relativos à raiz do projeto antigo — eles só são usados em retreino manual (documentado na Task 9) e não no runtime da API; não alterar a lógica deles neste plano.

- [ ] **Step 4: Escrever teste de sanidade dos artefatos**

`services/score-engine/tests/test_artifacts.py`:

```python
"""Sanidade: artefatos replicados carregam e produzem predição plausível."""
from pathlib import Path

import joblib
import pandas as pd

from score_engine.features.preprocessing import ALL_FEATURE_COLS

ARTIFACTS = Path(__file__).parents[1] / "artifacts"

# Linha bruta válida: omnívoro saudável × fruta — par sabidamente bem avaliado
SAMPLE_ROW = {
    "age": 35, "total_cholesterol": 180, "weight_kg": 70.0, "height_cm": 175.0, "bmi": 22.9,
    "diet_type": "omnivore", "goal": "maintenance", "activity_level": "moderately_active",
    "glycemic_condition": "none", "hypertension": "none",
    "allergy_gluten": 0, "allergy_lactose": 0, "allergy_nuts": 0,
    "allergy_shellfish": 0, "allergy_eggs": 0, "allergy_soy": 0,
    "restriction_low_sodium": 0, "restriction_low_sugar": 0, "restriction_low_fat": 0,
    "restriction_high_protein": 0, "restriction_low_carb": 0,
    "energy_kcal_100g": 52.0, "proteins_100g": 0.3, "carbohydrates_100g": 14.0,
    "fat_100g": 0.2, "saturated_fat_100g": 0.0, "fiber_100g": 2.4,
    "sodium_mg_100g": 1.0, "sugar_100g": 10.0,
    "food_group": "fruit",
    "contains_gluten": 0, "contains_lactose": 0, "contains_nuts": 0,
    "contains_shellfish": 0, "contains_eggs": 0, "contains_soy": 0,
    "is_animal_product": 0, "is_meat": 0, "is_fish": 0,
}


def test_artifacts_load_and_predict():
    model = joblib.load(ARTIFACTS / "mlp_model.pkl")
    preprocessor = joblib.load(ARTIFACTS / "preprocessor.pkl")

    df = pd.DataFrame([SAMPLE_ROW]).reindex(columns=ALL_FEATURE_COLS, fill_value=0)
    X = preprocessor.transform(df)
    pred = float(model.predict(X)[0])

    assert 0.0 <= pred <= 10.5  # saída bruta do MLP, antes do clip
    assert pred >= 5.0  # fruta para omnívoro saudável: score alto


def test_feature_columns_unchanged():
    # O contrato do preprocessador depende destas 36 colunas — mudou, quebrou o modelo
    assert len(ALL_FEATURE_COLS) == 36
```

- [ ] **Step 5: Instalar deps e rodar o teste**

```bash
cd services/score-engine && uv sync && uv run pytest tests/test_artifacts.py -v
```

Expected: 2 PASSED. Se `joblib.load` falhar por versão do sklearn, ajustar o pin no pyproject para a versão exata que abre os `.pkl` (`uv run python -c "import sklearn; print(sklearn.__version__)"` no venv do chall-ia revela a versão original).

- [ ] **Step 6: Commitar**

```bash
git add services/score-engine
git commit -m "feat(score-engine): replica código e artefatos do modelo do chall-ia"
```

---

### Task 3: scoring.py — heurística como fallback + breakdown de explicabilidade

**Files:**
- Create: `services/score-engine/src/score_engine/scoring.py`
- Test: `services/score-engine/tests/test_scoring.py`

- [ ] **Step 1: Escrever testes da heurística e do breakdown**

`services/score-engine/tests/test_scoring.py`:

```python
"""Heurística replicada: casos clínicos conhecidos + estrutura do breakdown."""
import pandas as pd

from score_engine.scoring import build_breakdown, compute_score
from tests.test_artifacts import SAMPLE_ROW

IND_COLS = [k for k in SAMPLE_ROW if not k.startswith(("energy", "proteins", "carbo", "fat",
            "saturated", "fiber", "sodium", "sugar", "food_group", "contains_", "is_"))]
FOOD_COLS = [k for k in SAMPLE_ROW if k not in IND_COLS]


def _ind(**overrides) -> pd.Series:
    return pd.Series({**{k: SAMPLE_ROW[k] for k in IND_COLS}, **overrides})


def _food(**overrides) -> pd.Series:
    return pd.Series({**{k: SAMPLE_ROW[k] for k in FOOD_COLS}, **overrides})


def test_allergen_zeroes_score():
    score = compute_score(_ind(allergy_nuts=1), _food(contains_nuts=1), noise_std=0.0)
    assert score == 0.0


def test_vegan_with_meat_is_penalized():
    base = compute_score(_ind(diet_type="vegan"), _food(), noise_std=0.0)
    meat = compute_score(_ind(diet_type="vegan"),
                         _food(is_animal_product=1, is_meat=1), noise_std=0.0)
    assert meat < base


def test_hypertension_with_sodium_is_penalized():
    base = compute_score(_ind(), _food(), noise_std=0.0)
    salty = compute_score(_ind(hypertension="uncontrolled"),
                          _food(sodium_mg_100g=800.0), noise_std=0.0)
    assert salty < base


def test_deterministic_without_noise():
    a = compute_score(_ind(), _food(), noise_std=0.0)
    b = compute_score(_ind(), _food(), noise_std=0.0)
    assert a == b


def test_breakdown_structure():
    bd = build_breakdown(_ind(allergy_nuts=1), _food(contains_nuts=1), heuristic_score=0.0)
    assert bd["allergen_safe"] is False
    assert set(bd) == {"allergen_safe", "diet_compatible", "goal_alignment",
                       "health_flags", "heuristic_reference"}
    assert bd["goal_alignment"] in {"high", "moderate", "low", "poor"}
```

- [ ] **Step 2: Rodar e ver falhar**

```bash
uv run pytest tests/test_scoring.py -v
```

Expected: FAIL — `ModuleNotFoundError: score_engine.scoring`.

- [ ] **Step 3: Implementar scoring.py**

`services/score-engine/src/score_engine/scoring.py`:

```python
"""
Heurística de score (replicada do chall-ia) e breakdown de explicabilidade.

A heurística é o ground truth do modelo MLP e o fallback em runtime.
O breakdown alimenta a transparência de resultado (SCRUM-19).
"""
import pandas as pd

# Re-export: a função canônica vive no pipeline de dados replicado (DRY)
from score_engine.data.generate_pairs import compute_score  # noqa: F401

ALLERGENS = ["gluten", "lactose", "nuts", "shellfish", "eggs", "soy"]


def build_breakdown(ind: pd.Series, food: pd.Series, heuristic_score: float) -> dict:
    """Explica o score de um par (portado de chall-ia src/api/main.py:_build_breakdown)."""
    hits = [a for a in ALLERGENS
            if ind.get(f"allergy_{a}", 0) and food.get(f"contains_{a}", 0)]
    allergen_safe = len(hits) == 0

    diet = ind.get("diet_type", "")
    diet_compat = True
    if diet == "vegan" and food.get("is_animal_product", 0):
        diet_compat = False
    elif diet == "vegetarian" and (food.get("is_meat", 0) or food.get("is_fish", 0)):
        diet_compat = False
    elif diet == "pescatarian" and food.get("is_meat", 0):
        diet_compat = False

    goal = ind.get("goal", "")
    protein = food.get("proteins_100g", 0)
    energy = food.get("energy_kcal_100g", 0)
    fiber = food.get("fiber_100g", 0)
    if goal == "muscle_gain" and protein >= 20:
        goal_alignment = "high"
    elif goal == "weight_loss" and energy < 200 and fiber > 3:
        goal_alignment = "high"
    elif goal == "health_improvement" and food.get("food_group") in ("vegetable", "fruit", "legume"):
        goal_alignment = "high"
    elif heuristic_score >= 7:
        goal_alignment = "moderate"
    elif heuristic_score >= 4:
        goal_alignment = "low"
    else:
        goal_alignment = "poor"

    flags: list[str] = []
    sodium = food.get("sodium_mg_100g", 0)
    sugar = food.get("sugar_100g", 0)
    sat_fat = food.get("saturated_fat_100g", 0)
    if ind.get("hypertension", "none") != "none" and sodium > 200:
        flags.append(f"sodium: caution ({sodium:.0f} mg/100g)")
    if ind.get("glycemic_condition", "none") != "none" and sugar > 8:
        flags.append(f"sugar: caution ({sugar:.1f} g/100g)")
    if ind.get("total_cholesterol", 0) > 240 and sat_fat > 5:
        flags.append(f"saturated fat: caution ({sat_fat:.1f} g/100g)")

    return {
        "allergen_safe": allergen_safe,
        "diet_compatible": diet_compat,
        "goal_alignment": goal_alignment,
        "health_flags": flags,
        "heuristic_reference": round(heuristic_score, 2),
    }
```

- [ ] **Step 4: Rodar e ver passar**

```bash
uv run pytest tests/test_scoring.py -v
```

Expected: 5 PASSED.

- [ ] **Step 5: Commitar**

```bash
git add src/score_engine/scoring.py tests/test_scoring.py
git commit -m "feat(score-engine): heurística como fallback e breakdown de explicabilidade"
```

---

### Task 4: mapping — perfil Helfy e alimento → features do modelo

**Files:**
- Create: `services/score-engine/src/score_engine/mapping/profile.py`
- Create: `services/score-engine/src/score_engine/mapping/food.py`
- Test: `services/score-engine/tests/test_mapping.py`

- [ ] **Step 1: Escrever testes do mapeamento**

`services/score-engine/tests/test_mapping.py`:

```python
"""Tradução perfil Helfy → features do modelo, e alimento Helfy → features."""
import pytest

from score_engine.features.preprocessing import ALL_FEATURE_COLS
from score_engine.mapping.food import map_food
from score_engine.mapping.profile import map_profile

HELFY_PROFILE = {
    "goal": "EMAGRECER", "diet_type": "vegetarian", "activity_level": "lightly_active",
    "age": 30, "weight_kg": 80.0, "height_cm": 170.0,
    "total_cholesterol": 210, "glucose": 110,
    "allergies": ["lactose"], "restrictions": ["low_sugar"],
}

HELFY_FOOD = {
    "food_id": "abc-123", "food_group": "dairy",
    "nutrition": {"energy_kcal_100g": 61.0, "proteins_100g": 3.3,
                  "carbohydrates_100g": 4.7, "fat_100g": 3.3,
                  "saturated_fat_100g": 1.9, "fiber_100g": 0.0,
                  "sodium_mg_100g": 40.0, "sugar_100g": 4.7},
    "allergen_flags": ["lactose"], "flags": ["animal_product"],
}


def test_goal_is_translated():
    assert map_profile(HELFY_PROFILE)["goal"] == "weight_loss"
    assert map_profile({**HELFY_PROFILE, "goal": "GANHAR_MASSA"})["goal"] == "muscle_gain"
    assert map_profile({**HELFY_PROFILE, "goal": "MANTER"})["goal"] == "maintenance"


@pytest.mark.parametrize("glucose,expected", [
    (None, "none"), (90, "none"), (100, "pre_diabetic"),
    (125, "pre_diabetic"), (126, "type_2"), (200, "type_2"),
])
def test_glucose_maps_to_glycemic_condition(glucose, expected):
    row = map_profile({**HELFY_PROFILE, "glucose": glucose})
    assert row["glycemic_condition"] == expected


def test_bmi_is_computed():
    assert map_profile(HELFY_PROFILE)["bmi"] == pytest.approx(27.7, abs=0.05)


def test_allergies_and_restrictions_become_flags():
    row = map_profile(HELFY_PROFILE)
    assert row["allergy_lactose"] == 1
    assert row["allergy_gluten"] == 0
    assert row["restriction_low_sugar"] == 1
    assert row["restriction_low_carb"] == 0


def test_defaults_for_missing_health_data():
    row = map_profile({**HELFY_PROFILE, "total_cholesterol": None, "glucose": None})
    assert row["total_cholesterol"] == 180  # mediana populacional como default
    assert row["glycemic_condition"] == "none"
    assert row["hypertension"] == "none"  # Sprint 1 não coleta pressão arterial


def test_food_mapping_produces_model_columns():
    row = map_food(HELFY_FOOD)
    assert row["food_id"] == "abc-123"
    assert row["energy_kcal_100g"] == 61.0
    assert row["contains_lactose"] == 1
    assert row["contains_gluten"] == 0
    assert row["is_animal_product"] == 1
    assert row["is_meat"] == 0


def test_profile_plus_food_covers_all_model_columns():
    merged = {**map_profile(HELFY_PROFILE), **map_food(HELFY_FOOD)}
    missing = [c for c in ALL_FEATURE_COLS if c not in merged]
    assert missing == []
```

- [ ] **Step 2: Rodar e ver falhar**

```bash
uv run pytest tests/test_mapping.py -v
```

Expected: FAIL — `ModuleNotFoundError: score_engine.mapping.profile`.

- [ ] **Step 3: Implementar profile.py e food.py**

`services/score-engine/src/score_engine/mapping/profile.py`:

```python
"""
Traduz o perfil Helfy (domínio do produto) para a linha de features do modelo.

Defaults documentados (spec §4.2):
- total_cholesterol ausente → 180 (mediana populacional)
- glucose ausente → glycemic_condition "none"
- hypertension → sempre "none" (o perfil da Sprint 1 não coleta pressão arterial)
"""
GOAL_MAP = {
    "EMAGRECER": "weight_loss",
    "GANHAR_MASSA": "muscle_gain",
    "MANTER": "maintenance",
}

VALID_ALLERGENS = ["gluten", "lactose", "nuts", "shellfish", "eggs", "soy"]
VALID_RESTRICTIONS = ["low_sodium", "low_sugar", "low_fat", "high_protein", "low_carb"]

DEFAULT_CHOLESTEROL = 180


def glycemic_condition_from_glucose(glucose: int | None) -> str:
    """Faixas clínicas de glicemia de jejum (mg/dL)."""
    if glucose is None or glucose < 100:
        return "none"
    if glucose < 126:
        return "pre_diabetic"
    return "type_2"


def map_profile(profile: dict) -> dict:
    height_m = profile["height_cm"] / 100
    bmi = round(profile["weight_kg"] / height_m**2, 1)

    row = {
        "age": profile["age"],
        "total_cholesterol": profile.get("total_cholesterol") or DEFAULT_CHOLESTEROL,
        "weight_kg": profile["weight_kg"],
        "height_cm": profile["height_cm"],
        "bmi": bmi,
        "diet_type": profile.get("diet_type") or "omnivore",
        "goal": GOAL_MAP[profile["goal"]],
        "activity_level": profile.get("activity_level") or "lightly_active",
        "glycemic_condition": glycemic_condition_from_glucose(profile.get("glucose")),
        "hypertension": "none",
    }

    allergies = set(profile.get("allergies") or [])
    restrictions = set(profile.get("restrictions") or [])
    for allergen in VALID_ALLERGENS:
        row[f"allergy_{allergen}"] = int(allergen in allergies)
    for restriction in VALID_RESTRICTIONS:
        row[f"restriction_{restriction}"] = int(restriction in restrictions)
    return row
```

`services/score-engine/src/score_engine/mapping/food.py`:

```python
"""Traduz o alimento Helfy (nutrition + flags) para a linha de features do modelo."""
from score_engine.features.preprocessing import FOOD_NUM
from score_engine.mapping.profile import VALID_ALLERGENS

FOOD_FLAGS = ["animal_product", "meat", "fish"]


def map_food(food: dict) -> dict:
    nutrition = food.get("nutrition") or {}
    row = {
        "food_id": food["food_id"],
        "food_group": food.get("food_group") or "other",
    }
    for col in FOOD_NUM:
        row[col] = float(nutrition.get(col) or 0.0)

    allergens = set(food.get("allergen_flags") or [])
    for allergen in VALID_ALLERGENS:
        row[f"contains_{allergen}"] = int(allergen in allergens)

    flags = set(food.get("flags") or [])
    for flag in FOOD_FLAGS:
        row[f"is_{flag}"] = int(flag in flags)
    return row
```

- [ ] **Step 4: Rodar e ver passar**

```bash
uv run pytest tests/test_mapping.py -v
```

Expected: 13 PASSED (6 são parametrizações da glicose).

- [ ] **Step 5: Commitar**

```bash
git add src/score_engine/mapping tests/test_mapping.py
git commit -m "feat(score-engine): mapeamento perfil/alimento Helfy para features do modelo"
```

---

### Task 5: ScoreEngine — predição em lote, normalização 0–1 e fallback

**Files:**
- Create: `services/score-engine/src/score_engine/service.py`
- Test: `services/score-engine/tests/test_service.py`

- [ ] **Step 1: Escrever testes do serviço**

`services/score-engine/tests/test_service.py`:

```python
"""ScoreEngine: lote, escala 0–1, fallback heurístico explícito."""
from pathlib import Path

from score_engine.mapping.food import map_food
from score_engine.mapping.profile import map_profile
from score_engine.service import ScoreEngine
from tests.test_mapping import HELFY_FOOD, HELFY_PROFILE

ARTIFACTS = Path(__file__).parents[1] / "artifacts"


def test_scores_batch_in_unit_scale():
    engine = ScoreEngine(ARTIFACTS)
    assert engine.model_loaded

    profile_row = map_profile(HELFY_PROFILE)
    foods = [map_food(HELFY_FOOD), map_food({**HELFY_FOOD, "food_id": "xyz-789"})]

    results, engine_used = engine.score_pairs(profile_row, foods)

    assert engine_used == "mlp"
    assert [r["food_id"] for r in results] == ["abc-123", "xyz-789"]
    for r in results:
        assert 0.0 <= r["score"] <= 1.0
        assert "allergen_safe" in r["breakdown"]


def test_lactose_allergy_gives_zero_breakdown_unsafe():
    engine = ScoreEngine(ARTIFACTS)
    profile_row = map_profile({**HELFY_PROFILE, "allergies": ["lactose"]})
    results, _ = engine.score_pairs(profile_row, [map_food(HELFY_FOOD)])
    assert results[0]["breakdown"]["allergen_safe"] is False


def test_fallback_to_heuristic_when_artifacts_missing(tmp_path):
    engine = ScoreEngine(tmp_path)  # diretório sem .pkl
    assert not engine.model_loaded

    results, engine_used = engine.score_pairs(
        map_profile(HELFY_PROFILE), [map_food(HELFY_FOOD)]
    )
    assert engine_used == "heuristic"
    assert 0.0 <= results[0]["score"] <= 1.0
```

- [ ] **Step 2: Rodar e ver falhar**

```bash
uv run pytest tests/test_service.py -v
```

Expected: FAIL — `ModuleNotFoundError: score_engine.service`.

- [ ] **Step 3: Implementar service.py**

`services/score-engine/src/score_engine/service.py`:

```python
"""
Núcleo do serviço: carrega artefatos e pontua pares perfil × alimentos em lote.

O modelo prevê na escala 0–10 (escala de treino); a borda pública do Helfy
usa 0.0–1.0, então a normalização (÷10) acontece aqui, uma única vez.
"""
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from score_engine.features.preprocessing import ALL_FEATURE_COLS
from score_engine.scoring import build_breakdown, compute_score

logger = logging.getLogger(__name__)

MODEL_VERSION = "mlp-v1"


class ScoreEngine:
    def __init__(self, artifacts_dir: Path):
        self.model = None
        self.preprocessor = None
        try:
            self.model = joblib.load(artifacts_dir / "mlp_model.pkl")
            self.preprocessor = joblib.load(artifacts_dir / "preprocessor.pkl")
            logger.info("artefatos carregados de %s", artifacts_dir)
        except FileNotFoundError as exc:
            logger.warning("artefatos ausentes (%s) — operando em modo heurístico", exc)

    @property
    def model_loaded(self) -> bool:
        return self.model is not None and self.preprocessor is not None

    def score_pairs(
        self, profile_row: dict, food_rows: list[dict]
    ) -> tuple[list[dict], str]:
        """Retorna ([{food_id, score 0–1, breakdown}], "mlp" | "heuristic")."""
        ind = pd.Series(profile_row)

        if self.model_loaded:
            df = pd.DataFrame([{**profile_row, **food} for food in food_rows])
            df = df.reindex(columns=ALL_FEATURE_COLS, fill_value=0)
            X = self.preprocessor.transform(df)
            raw_scores = np.clip(self.model.predict(X), 0.0, 10.0)
            engine_used = "mlp"
        else:
            raw_scores = [
                compute_score(ind, pd.Series(food), noise_std=0.0) for food in food_rows
            ]
            engine_used = "heuristic"

        results = []
        for food_row, raw in zip(food_rows, raw_scores):
            food = pd.Series(food_row)
            heuristic = compute_score(ind, food, noise_std=0.0)
            results.append({
                "food_id": food_row["food_id"],
                "score": round(float(raw) / 10.0, 3),
                "breakdown": build_breakdown(ind, food, heuristic),
            })
        return results, engine_used
```

- [ ] **Step 4: Rodar e ver passar**

```bash
uv run pytest tests/test_service.py -v
```

Expected: 3 PASSED. Atenção: se `compute_score` levantar `KeyError` para alguma coluna que `map_profile`/`map_food` não produz, a correção é nos mappers (adicionar a coluna com default), nunca na heurística replicada.

- [ ] **Step 5: Commitar**

```bash
git add src/score_engine/service.py tests/test_service.py
git commit -m "feat(score-engine): predição em lote com escala 0-1 e fallback heurístico"
```

---

### Task 6: API FastAPI — POST /score, GET /health, OpenAPI

**Files:**
- Create: `services/score-engine/src/score_engine/api/schemas.py`
- Create: `services/score-engine/src/score_engine/api/main.py`
- Test: `services/score-engine/tests/test_api.py`

- [ ] **Step 1: Escrever testes da API**

`services/score-engine/tests/test_api.py`:

```python
"""Contrato HTTP da engine: /score, /health e geração do OpenAPI."""
from fastapi.testclient import TestClient

from score_engine.api.main import app
from tests.test_mapping import HELFY_FOOD, HELFY_PROFILE


def _client() -> TestClient:
    return TestClient(app)  # context manager dispara o lifespan


def test_health_reports_model_loaded():
    with _client() as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["model_version"] == "mlp-v1"


def test_score_batch_contract():
    with _client() as client:
        resp = client.post("/score", json={"profile": HELFY_PROFILE,
                                           "foods": [HELFY_FOOD]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["engine"] == "mlp"
    assert body["model_version"] == "mlp-v1"
    assert len(body["scores"]) == 1
    item = body["scores"][0]
    assert item["food_id"] == "abc-123"
    assert 0.0 <= item["score"] <= 1.0
    assert item["breakdown"]["allergen_safe"] is False  # perfil tem alergia a lactose


def test_score_rejects_empty_foods():
    with _client() as client:
        resp = client.post("/score", json={"profile": HELFY_PROFILE, "foods": []})
    assert resp.status_code == 422


def test_score_rejects_invalid_goal():
    with _client() as client:
        resp = client.post("/score", json={
            "profile": {**HELFY_PROFILE, "goal": "FICAR_FORTE"},
            "foods": [HELFY_FOOD],
        })
    assert resp.status_code == 422


def test_openapi_schema_is_generated():
    with _client() as client:
        resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "/score" in schema["paths"]
    assert "/health" in schema["paths"]
    assert schema["info"]["title"] == "Helfy Score Engine"
```

- [ ] **Step 2: Rodar e ver falhar**

```bash
uv run pytest tests/test_api.py -v
```

Expected: FAIL — `ModuleNotFoundError: score_engine.api.main`.

- [ ] **Step 3: Implementar schemas.py**

`services/score-engine/src/score_engine/api/schemas.py`:

```python
"""Schemas do contrato público da engine — com exemplos para o OpenAPI (spec §7)."""
from typing import Literal

from pydantic import BaseModel, Field

PROFILE_EXAMPLE = {
    "goal": "EMAGRECER", "diet_type": "vegetarian", "activity_level": "lightly_active",
    "age": 30, "weight_kg": 80.0, "height_cm": 170.0,
    "total_cholesterol": 210, "glucose": 110,
    "allergies": ["lactose"], "restrictions": ["low_sugar"],
}

FOOD_EXAMPLE = {
    "food_id": "abc-123", "food_group": "dairy",
    "nutrition": {"energy_kcal_100g": 61.0, "proteins_100g": 3.3,
                  "carbohydrates_100g": 4.7, "fat_100g": 3.3,
                  "saturated_fat_100g": 1.9, "fiber_100g": 0.0,
                  "sodium_mg_100g": 40.0, "sugar_100g": 4.7},
    "allergen_flags": ["lactose"], "flags": ["animal_product"],
}


class ProfileIn(BaseModel):
    """Perfil de saúde no vocabulário do Helfy (a engine traduz para o modelo)."""
    goal: Literal["EMAGRECER", "GANHAR_MASSA", "MANTER"]
    diet_type: Literal["omnivore", "vegetarian", "vegan", "keto",
                       "pescatarian", "paleo"] = "omnivore"
    activity_level: Literal["sedentary", "lightly_active", "moderately_active",
                            "very_active"] = "lightly_active"
    age: int = Field(ge=18, le=110)
    weight_kg: float = Field(gt=30, le=300)
    height_cm: float = Field(gt=100, le=250)
    total_cholesterol: int | None = Field(default=None, ge=100, le=400)
    glucose: int | None = Field(default=None, ge=40, le=500,
                                description="Glicemia de jejum em mg/dL")
    allergies: list[Literal["gluten", "lactose", "nuts", "shellfish",
                            "eggs", "soy"]] = []
    restrictions: list[Literal["low_sodium", "low_sugar", "low_fat",
                               "high_protein", "low_carb"]] = []

    model_config = {"json_schema_extra": {"examples": [PROFILE_EXAMPLE]}}


class FoodIn(BaseModel):
    """Alimento com info nutricional por 100g, nas chaves canônicas da engine."""
    food_id: str
    food_group: str = "other"
    nutrition: dict[str, float] = Field(
        description="Chaves: energy_kcal_100g, proteins_100g, carbohydrates_100g, "
                    "fat_100g, saturated_fat_100g, fiber_100g, sodium_mg_100g, sugar_100g")
    allergen_flags: list[str] = []
    flags: list[Literal["animal_product", "meat", "fish"]] = []

    model_config = {"json_schema_extra": {"examples": [FOOD_EXAMPLE]}}


class ScoreRequest(BaseModel):
    profile: ProfileIn
    foods: list[FoodIn] = Field(min_length=1)


class Breakdown(BaseModel):
    allergen_safe: bool
    diet_compatible: bool
    goal_alignment: Literal["high", "moderate", "low", "poor"]
    health_flags: list[str]
    heuristic_reference: float = Field(description="Score da heurística na escala 0–10")


class ScoreItem(BaseModel):
    food_id: str
    score: float = Field(ge=0.0, le=1.0)
    breakdown: Breakdown


class ScoreResponse(BaseModel):
    scores: list[ScoreItem]
    model_version: str
    engine: Literal["mlp", "heuristic"] = Field(
        description="'heuristic' indica fallback por falha no carregamento do modelo")


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str
```

- [ ] **Step 4: Implementar api/main.py**

`services/score-engine/src/score_engine/api/main.py`:

```python
"""
Helfy Score Engine — API stateless de score nutricional.

Recebe perfil Helfy + alimentos no request; não persiste nada (spec §2).
Swagger UI em /docs, ReDoc em /redoc (spec §7).
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from score_engine.api.schemas import (
    HealthResponse,
    ScoreRequest,
    ScoreResponse,
)
from score_engine.mapping.food import map_food
from score_engine.mapping.profile import map_profile
from score_engine.service import MODEL_VERSION, ScoreEngine

logging.basicConfig(level=logging.INFO,
                    format='{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}')

# api/ → score_engine → src → score-engine (raiz do serviço)
ARTIFACTS_DIR = Path(__file__).parents[3] / "artifacts"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = ScoreEngine(ARTIFACTS_DIR)
    yield


app = FastAPI(
    title="Helfy Score Engine",
    description="Score de compatibilidade nutricional (0.0–1.0) por par usuário × alimento. "
                "Serviço stateless: o perfil e os alimentos chegam no corpo da requisição.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["system"],
         summary="Status do serviço e do modelo")
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=app.state.engine.model_loaded,
        model_version=MODEL_VERSION,
    )


@app.post("/score", response_model=ScoreResponse, tags=["score"],
          summary="Pontua um lote de alimentos para um perfil")
def score(body: ScoreRequest) -> ScoreResponse:
    profile_row = map_profile(body.profile.model_dump())
    food_rows = [map_food(food.model_dump()) for food in body.foods]
    results, engine_used = app.state.engine.score_pairs(profile_row, food_rows)
    return ScoreResponse(scores=results, model_version=MODEL_VERSION, engine=engine_used)
```

- [ ] **Step 5: Rodar e ver passar**

```bash
uv run pytest tests/test_api.py -v
```

Expected: 5 PASSED.

- [ ] **Step 6: Rodar a suíte inteira + lint**

```bash
uv run ruff check . && uv run pytest -v
```

Expected: lint limpo, todos os testes PASSED.

- [ ] **Step 7: Subir localmente e conferir o Swagger**

```bash
uv run uvicorn score_engine.api.main:app --port 8001 &
sleep 2 && curl -s localhost:8001/health && curl -s localhost:8001/docs -o /dev/null -w "%{http_code}\n"
kill %1
```

Expected: health com `"model_loaded":true`; `/docs` retorna 200.

- [ ] **Step 8: Commitar**

```bash
git add src/score_engine/api tests/test_api.py
git commit -m "feat(score-engine): API /score e /health com OpenAPI documentado"
```

---

### Task 7: Dockerfile + docker-compose (postgres + score-engine)

**Files:**
- Create: `services/score-engine/Dockerfile`
- Create: `services/score-engine/.dockerignore`
- Create: `docker-compose.yml` (raiz)
- Create: `.env.example` (raiz)

- [ ] **Step 1: Criar Dockerfile e .dockerignore**

`services/score-engine/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ src/
COPY artifacts/ artifacts/

EXPOSE 8001
CMD ["uv", "run", "--no-sync", "uvicorn", "score_engine.api.main:app", \
     "--host", "0.0.0.0", "--port", "8001"]
```

`services/score-engine/.dockerignore`:

```
.venv/
tests/
__pycache__/
.pytest_cache/
.ruff_cache/
data/
```

- [ ] **Step 2: Criar docker-compose.yml na raiz**

```yaml
# Infra local do Helfy. core-api entra no Plano 2.
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-helfy}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-helfy}
      POSTGRES_DB: ${POSTGRES_DB:-helfy}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U helfy"]
      interval: 5s
      timeout: 3s
      retries: 10

  score-engine:
    build: services/score-engine
    ports:
      - "8001:8001"
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request as u; u.urlopen('http://localhost:8001/health')\""]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

`.env.example` (raiz):

```bash
POSTGRES_USER=helfy
POSTGRES_PASSWORD=helfy
POSTGRES_DB=helfy
```

- [ ] **Step 3: Build e smoke test**

```bash
cd /home/bcr/estudos/helfy
docker compose up --build -d
sleep 10
curl -s localhost:8001/health
curl -s -X POST localhost:8001/score -H 'Content-Type: application/json' -d '{
  "profile": {"goal":"EMAGRECER","age":30,"weight_kg":80,"height_cm":170},
  "foods": [{"food_id":"f1","food_group":"fruit",
             "nutrition":{"energy_kcal_100g":52,"proteins_100g":0.3,"carbohydrates_100g":14,
                          "fat_100g":0.2,"saturated_fat_100g":0,"fiber_100g":2.4,
                          "sodium_mg_100g":1,"sugar_100g":10}}]}'
docker compose down
```

Expected: health com `"model_loaded":true`; score entre 0 e 1 com `"engine":"mlp"`. Se o build falhar por falta de `uv.lock`, gerar antes com `cd services/score-engine && uv lock`.

- [ ] **Step 4: Commitar**

```bash
git add services/score-engine/Dockerfile services/score-engine/.dockerignore \
        docker-compose.yml .env.example services/score-engine/uv.lock
git commit -m "feat: docker-compose com postgres e score-engine dockerizado"
```

---

### Task 8: CI — GitHub Actions

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Criar o workflow**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  score-engine:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/score-engine
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Instalar dependências
        run: uv sync
      - name: Lint
        run: uv run ruff check .
      - name: Testes
        run: uv run pytest -v
# Job da core-api entra no Plano 2; do mobile, no Plano 3.
```

- [ ] **Step 2: Validar sintaxe localmente e commitar**

```bash
docker run --rm -v "$PWD":/repo rhysd/actionlint:latest -color /repo/.github/workflows/ci.yml \
  || uv run python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml')); print('yaml ok')"
git add .github/workflows/ci.yml
git commit -m "ci: pipeline de lint e testes do score-engine"
```

Expected: sem erros de sintaxe. (Se não houver remote/GitHub ainda, o job roda no primeiro push.)

---

### Task 9: Documentação do serviço e migração do approach.md

**Files:**
- Copy: `chall-ia/docs/approach.md` → `docs/approach.md`
- Create: `services/score-engine/README.md`

- [ ] **Step 1: Migrar approach.md com nota de contexto**

```bash
cp /home/bcr/estudos/checkpoints/chall-ia/docs/approach.md docs/approach.md
```

Adicionar no topo do arquivo copiado (antes do conteúdo original):

```markdown
> **Nota (2026-06-11):** documento herdado do projeto original (chall-ia), que descreve
> o treinamento do modelo replicado em `services/score-engine/`. Diferenças no Helfy:
> a API é stateless (sem `/individuals`), o contrato é `POST /score` em lote com
> score normalizado para 0.0–1.0, e o perfil chega no vocabulário do Helfy
> (ver `docs/superpowers/specs/2026-06-11-helfy-monorepo-design.md`, seção 4).
```

- [ ] **Step 2: Criar README do serviço**

`services/score-engine/README.md`:

```markdown
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
```

- [ ] **Step 3: Suíte final e commit**

```bash
cd services/score-engine && uv run pytest -v && uv run ruff check . && cd ../..
git add docs/approach.md services/score-engine/README.md
git commit -m "docs: migra approach.md do chall-ia e documenta o score-engine"
```

Expected: todos os testes PASSED antes do commit.

---

## Critérios de aceite do plano (verificação final)

- [ ] `docker compose up --build` sobe postgres + score-engine saudáveis
- [ ] `POST /score` com perfil Helfy retorna scores 0–1 com breakdown (`engine: "mlp"`)
- [ ] `/docs`, `/redoc` e `/openapi.json` servidos pela engine (spec §7)
- [ ] Suíte pytest verde (artefatos, heurística, mapping, service, API) + ruff limpo
- [ ] CI configurado
- [ ] Nenhum commit com trailer de IA
