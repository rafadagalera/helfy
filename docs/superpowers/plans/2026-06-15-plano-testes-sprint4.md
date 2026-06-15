# Plano de Testes e Automação (Sprint 4) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o pacote de testes da Sprint 4 — plano manual (Markdown + CSV importável no Azure Boards) e automação Postman determinística (~12 casos) que passa 100% no `newman` contra a core-api local — tudo na branch `develop`.

**Architecture:** Manual valida a camada de UI/sistema (app + Swagger) e os fluxos não-determinísticos (barcode, receita real com seed). Automação valida o contrato e a lógica da API por um caminho self-contained (cria seus próprios dados, sem depender de seed nem de rede externa). Collection Postman v2.1 hand-authored, versionada no repo, executável via Collection Runner (vídeo) e `newman` (CLI).

**Tech Stack:** Postman Collection v2.1 + `newman` (via `npx`), Markdown, CSV (Azure Boards Test Case import), Docker Compose (core-api + score-engine + postgres).

---

## File Structure

| Caminho | Responsabilidade |
|---|---|
| `docs/testing/2026-06-15-plano-testes-sprint4.md` | Plano mestre legível: Parte A (12 casos), descrição da Parte B, justificativa Postman |
| `tests/manual/azure-boards-testcases.csv` | Test Cases importáveis no Azure Boards (com steps) |
| `tests/postman/helfy.postman_environment.json` | Variáveis: `baseUrl`, `password`, e slots para `email/userId/token/foodId` |
| `tests/postman/helfy.postman_collection.json` | Collection v2.1 com ~12 requests + asserções `pm.test` |
| `tests/postman/README.md` | Instruções de execução (Runner + newman) + roteiro do vídeo |
| `README.md` (raiz) | Apontar para os artefatos de teste |

---

### Task 1: Criar e publicar a branch `develop`

**Files:** nenhum (operação git)

- [ ] **Step 1: Criar a branch a partir de `main`**

```bash
cd /home/bcr/estudos/helfy
git checkout -b develop
```

- [ ] **Step 2: Publicar a branch no remoto**

```bash
git push -u origin develop
```
Expected: `* [new branch] develop -> develop` e tracking configurado.

- [ ] **Step 3: Confirmar identidade git (conta pessoal)**

Run: `git config user.email`
Expected: `dagalera.dev@gmail.com`

---

### Task 2: Plano de testes manuais (Markdown)

**Files:**
- Create: `docs/testing/2026-06-15-plano-testes-sprint4.md`

- [ ] **Step 1: Criar o documento com cabeçalho, justificativa e os 12 casos**

Crie `docs/testing/2026-06-15-plano-testes-sprint4.md` com EXATAMENTE este conteúdo:

````markdown
# Plano de Testes — Helfy (Sprint 4)

> Validação a nível de sistema das funcionalidades principais do Helfy.
> Testes manuais (Parte A) executados contra o app mobile (Expo) e o Swagger UI (`/docs`).
> Automação (Parte B) em `tests/postman/`. Dados controlados e predefinidos.

## Ambiente de teste

- Backend: `docker compose up` (core-api em `http://localhost:8000`, Swagger em `/docs`).
  O start executa migrations + seed automaticamente (alimentos e receitas pré-cadastrados).
- App mobile: `cd apps/mobile && npm install && npx expo start`, com
  `EXPO_PUBLIC_API_URL=http://<ip-da-maquina>:8000` em `apps/mobile/.env`.
- Usuário-base dos testes: `teste.helfy@example.com` / `Senha@12345`.

## Parte B — nota sobre cobertura de UI

O Helfy possui app mobile, mas é um **cliente fino**: toda a lógica de negócio, validação,
score e regras de receita reside na `core-api`. A automação (Postman) exercita o núcleo do
sistema de ponta a ponta; a camada de UI é validada manualmente nos casos abaixo.

## Casos de teste

### TC-01 — Registro de novo usuário
- **Pré-condições:** e-mail `teste.helfy@example.com` ainda não cadastrado.
- **Dados de entrada:** nome=`Teste Helfy`, email=`teste.helfy@example.com`, senha=`Senha@12345`.
- **Saída esperada:** conta criada (HTTP 201); app faz login automático e abre a Home.
- **Passos:**
  1. Abrir o app na tela inicial.
  2. Tocar em "Criar conta".
  3. Preencher nome, e-mail e senha.
  4. Tocar em "Cadastrar".
  5. Verificar redirecionamento autenticado para a Home.

### TC-02 — Registro com e-mail já existente
- **Pré-condições:** `teste.helfy@example.com` já registrado (TC-01).
- **Dados de entrada:** nome=`Outro`, email=`teste.helfy@example.com`, senha=`Senha@12345`.
- **Saída esperada:** erro "E-mail já cadastrado" (HTTP 409); permanece na tela de cadastro.
- **Passos:**
  1. Abrir "Criar conta".
  2. Preencher com o e-mail já usado.
  3. Tocar em "Cadastrar".
  4. Verificar mensagem de erro de e-mail duplicado.

### TC-03 — Login com credenciais válidas
- **Pré-condições:** usuário do TC-01 existe.
- **Dados de entrada:** email=`teste.helfy@example.com`, senha=`Senha@12345`.
- **Saída esperada:** sessão autenticada (token JWT armazenado); Home carrega.
- **Passos:**
  1. Na tela de login, preencher e-mail e senha.
  2. Tocar em "Entrar".
  3. Verificar abertura da Home com receitas sugeridas.

### TC-04 — Login com senha incorreta
- **Pré-condições:** usuário do TC-01 existe.
- **Dados de entrada:** email=`teste.helfy@example.com`, senha=`senhaErrada`.
- **Saída esperada:** erro "Credenciais inválidas" (HTTP 401); sem sessão.
- **Passos:**
  1. Preencher e-mail correto e senha errada.
  2. Tocar em "Entrar".
  3. Verificar mensagem de credenciais inválidas.

### TC-05 — Completar perfil / onboarding
- **Pré-condições:** logado (TC-03).
- **Dados de entrada:** idade=`30`, altura=`170`, peso=`80`, objetivo=`EMAGRECER`,
  dieta=`vegetarian`, restrição=`low_sugar`, alergia=`lactose`, colesterol=`210`, glicose=`110`.
- **Saída esperada:** perfil salvo (HTTP 200); dados refletidos na tela de perfil.
- **Passos:**
  1. Abrir a aba de Perfil.
  2. Preencher idade, altura, peso e objetivo.
  3. Selecionar dieta, restrição e alergia.
  4. Informar colesterol e glicose.
  5. Salvar e verificar persistência dos dados.

### TC-06 — Perfil com peso fora do intervalo
- **Pré-condições:** logado.
- **Dados de entrada:** peso=`10` (abaixo do mínimo permitido de 30 kg).
- **Saída esperada:** validação impede o salvamento (HTTP 422); campo sinalizado.
- **Passos:**
  1. Abrir Perfil.
  2. Informar peso=`10`.
  3. Tentar salvar.
  4. Verificar mensagem/realce de validação.

### TC-07 — Adicionar alimento por scan de barcode
- **Pré-condições:** logado; produto com barcode existente no Open Food Facts.
- **Dados de entrada:** código de barras `7894900011517` (Coca-Cola, exemplo OFF).
- **Saída esperada:** alimento encontrado e adicionado à dispensa (HTTP 201); aparece na lista.
- **Passos:**
  1. Abrir a Dispensa.
  2. Tocar em "Adicionar" → "Escanear".
  3. Escanear/digitar o código de barras.
  4. Confirmar a adição.
  5. Verificar o item na dispensa.

### TC-08 — Adicionar alimento por input manual
- **Pré-condições:** logado.
- **Dados de entrada:** nome=`Banana`, grupo=`fruit`, calorias/100g=`89`.
- **Saída esperada:** alimento criado e adicionado (HTTP 201); aparece na lista.
- **Passos:**
  1. Abrir a Dispensa.
  2. Tocar em "Adicionar" → "Manual".
  3. Preencher nome, grupo e informação nutricional.
  4. Confirmar.
  5. Verificar o item na dispensa.

### TC-09 — Remover alimento da dispensa
- **Pré-condições:** dispensa contém ao menos o item do TC-08.
- **Dados de entrada:** alimento `Banana`.
- **Saída esperada:** item removido (HTTP 204); some da lista.
- **Passos:**
  1. Abrir a Dispensa.
  2. Acionar a remoção do item `Banana`.
  3. Confirmar.
  4. Verificar que o item não está mais listado.

### TC-10 — Ver score nutricional e justificativa
- **Pré-condições:** perfil cadastrado (TC-05); dispensa com ao menos 1 alimento.
- **Dados de entrada:** alimento da dispensa (ex: `Banana`).
- **Saída esperada:** score entre 0.0 e 1.0 exibido com justificativa textual (SCRUM-19).
- **Passos:**
  1. Abrir a Dispensa.
  2. Selecionar um alimento.
  3. Verificar o score exibido.
  4. Abrir/verificar a justificativa do score.

### TC-11 — Ver receitas sugeridas
- **Pré-condições:** perfil cadastrado; dispensa com alimentos do seed
  (ex: arroz integral, feijão preto, peito de frango).
- **Dados de entrada:** dispensa contendo os 3 alimentos acima.
- **Saída esperada:** lista de receitas viáveis (cobertura ≥70%), ex: "Arroz com feijão e frango grelhado".
- **Passos:**
  1. Adicionar arroz integral, feijão preto e peito de frango à dispensa.
  2. Abrir a Home / aba de receitas.
  3. Verificar receitas sugeridas exibidas.
  4. Conferir que pelo menos uma receita viável aparece.

### TC-12 — Receitas sem perfil cadastrado
- **Pré-condições:** novo usuário logado, SEM perfil cadastrado.
- **Dados de entrada:** nenhum (apenas requisição de sugestões).
- **Saída esperada:** bloqueio com mensagem para cadastrar o perfil (HTTP 409).
- **Passos:**
  1. Registrar/logar um usuário novo.
  2. Sem preencher o perfil, abrir a tela de receitas.
  3. Verificar a mensagem solicitando cadastro de perfil.
````

- [ ] **Step 2: Verificar que não há placeholders e que todos os 5 fluxos estão cobertos**

Run: `grep -c '^### TC-' docs/testing/2026-06-15-plano-testes-sprint4.md`
Expected: `12`

- [ ] **Step 3: Commit**

```bash
git add docs/testing/2026-06-15-plano-testes-sprint4.md
git commit -m "docs(testes): plano de testes manuais da Sprint 4 (12 casos)"
```

---

### Task 3: CSV importável no Azure Boards

**Files:**
- Create: `tests/manual/azure-boards-testcases.csv`

- [ ] **Step 1: Criar o CSV no formato de import do Azure Boards**

O formato do Azure DevOps para Test Cases com passos: a primeira linha de cada caso traz
`Work Item Type=Test Case` + `Title` + `Step 1`; linhas seguintes do mesmo caso deixam
`Work Item Type` e `Title` vazios e trazem os demais passos. Crie
`tests/manual/azure-boards-testcases.csv` com EXATAMENTE este conteúdo:

```csv
Work Item Type,Title,Test Step,Step Action,Step Expected,Tags
Test Case,TC-01 Registro de novo usuario,1,"Abrir o app na tela inicial","Tela inicial visivel",Auth
,,2,"Tocar em Criar conta","Formulario de cadastro exibido",
,,3,"Preencher nome=Teste Helfy, email=teste.helfy@example.com, senha=Senha@12345","Campos preenchidos",
,,4,"Tocar em Cadastrar","Conta criada (HTTP 201) e login automatico",
,,5,"Observar a navegacao","Home carregada autenticada",
Test Case,TC-02 Registro com email existente,1,"Abrir Criar conta","Formulario exibido",Auth
,,2,"Preencher email=teste.helfy@example.com (ja usado)","Campos preenchidos",
,,3,"Tocar em Cadastrar","Erro E-mail ja cadastrado (HTTP 409)",
Test Case,TC-03 Login com credenciais validas,1,"Tela de login","Formulario de login exibido",Auth
,,2,"Preencher email=teste.helfy@example.com, senha=Senha@12345","Campos preenchidos",
,,3,"Tocar em Entrar","Sessao autenticada, Home carregada",
Test Case,TC-04 Login com senha incorreta,1,"Tela de login","Formulario exibido",Auth
,,2,"Preencher email correto e senha=senhaErrada","Campos preenchidos",
,,3,"Tocar em Entrar","Erro Credenciais invalidas (HTTP 401)",
Test Case,TC-05 Completar perfil onboarding,1,"Abrir aba Perfil","Tela de perfil exibida",Perfil
,,2,"Preencher idade=30, altura=170, peso=80, objetivo=EMAGRECER","Campos preenchidos",
,,3,"Selecionar dieta=vegetarian, restricao=low_sugar, alergia=lactose","Selecoes aplicadas",
,,4,"Informar colesterol=210, glicose=110","Campos preenchidos",
,,5,"Salvar","Perfil salvo (HTTP 200) e dados persistidos",
Test Case,TC-06 Perfil com peso invalido,1,"Abrir Perfil","Tela exibida",Perfil
,,2,"Informar peso=10","Valor abaixo do minimo (30 kg)",
,,3,"Tentar salvar","Validacao impede salvar (HTTP 422)",
Test Case,TC-07 Adicionar alimento por barcode,1,"Abrir Dispensa","Tela da dispensa exibida",Dispensa
,,2,"Adicionar -> Escanear","Leitor/entrada de codigo exibido",
,,3,"Informar codigo 7894900011517","Produto localizado no Open Food Facts",
,,4,"Confirmar adicao","Item adicionado (HTTP 201) e listado",
Test Case,TC-08 Adicionar alimento manual,1,"Abrir Dispensa","Tela exibida",Dispensa
,,2,"Adicionar -> Manual","Formulario manual exibido",
,,3,"Preencher nome=Banana, grupo=fruit, calorias/100g=89","Campos preenchidos",
,,4,"Confirmar","Item criado e adicionado (HTTP 201)",
Test Case,TC-09 Remover alimento da dispensa,1,"Abrir Dispensa com item Banana","Item visivel",Dispensa
,,2,"Acionar remocao do item Banana","Confirmacao solicitada",
,,3,"Confirmar remocao","Item removido (HTTP 204) e fora da lista",
Test Case,TC-10 Ver score e justificativa,1,"Abrir Dispensa","Itens com score exibidos",Score
,,2,"Selecionar um alimento (ex Banana)","Detalhe do alimento",
,,3,"Verificar score","Valor entre 0.0 e 1.0 exibido",
,,4,"Abrir justificativa","Texto explicativo do score (SCRUM-19)",
Test Case,TC-11 Ver receitas sugeridas,1,"Adicionar arroz integral, feijao preto e peito de frango","Itens na dispensa",Receitas
,,2,"Abrir Home / aba de receitas","Lista de sugestoes carregada",
,,3,"Conferir sugestoes","Ao menos 1 receita viavel (cobertura >=70%) exibida",
Test Case,TC-12 Receitas sem perfil,1,"Logar usuario novo sem perfil","Sessao autenticada sem perfil",Receitas
,,2,"Abrir tela de receitas","Requisicao de sugestoes disparada",
,,3,"Observar resposta","Bloqueio pedindo cadastro de perfil (HTTP 409)",
```

- [ ] **Step 2: Verificar contagem de casos no CSV**

Run: `grep -c '^Test Case,' tests/manual/azure-boards-testcases.csv`
Expected: `12`

- [ ] **Step 3: Commit**

```bash
git add tests/manual/azure-boards-testcases.csv
git commit -m "test(manual): CSV de Test Cases importavel no Azure Boards"
```

---

### Task 4: Environment do Postman

**Files:**
- Create: `tests/postman/helfy.postman_environment.json`

- [ ] **Step 1: Criar o environment**

Crie `tests/postman/helfy.postman_environment.json` com EXATAMENTE este conteúdo:

```json
{
  "id": "helfy-local-env",
  "name": "Helfy Local",
  "values": [
    { "key": "baseUrl", "value": "http://localhost:8000", "type": "default", "enabled": true },
    { "key": "password", "value": "Senha@12345", "type": "default", "enabled": true },
    { "key": "email", "value": "", "type": "default", "enabled": true },
    { "key": "userId", "value": "", "type": "default", "enabled": true },
    { "key": "token", "value": "", "type": "default", "enabled": true },
    { "key": "foodId", "value": "", "type": "default", "enabled": true }
  ],
  "_postman_variable_scope": "environment"
}
```

- [ ] **Step 2: Validar JSON**

Run: `python3 -c "import json; json.load(open('tests/postman/helfy.postman_environment.json')); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add tests/postman/helfy.postman_environment.json
git commit -m "test(postman): environment local do Helfy"
```

---

### Task 5: Collection do Postman (~12 casos com asserções)

**Files:**
- Create: `tests/postman/helfy.postman_collection.json`

- [ ] **Step 1: Criar a collection v2.1 com todos os requests e `pm.test`**

Crie `tests/postman/helfy.postman_collection.json` com EXATAMENTE este conteúdo:

```json
{
  "info": {
    "name": "Helfy Core API — Sprint 4",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    "description": "Automacao deterministica do fluxo Helfy: auth -> perfil -> dispensa -> score -> receitas. Cria seus proprios dados; nao depende de seed nem de rede externa."
  },
  "auth": { "type": "bearer", "bearer": [ { "key": "token", "value": "{{token}}", "type": "string" } ] },
  "item": [
    {
      "name": "A1 Register (201)",
      "event": [
        { "listen": "prerequest", "script": { "type": "text/javascript", "exec": [
          "pm.environment.set('email', 'helfy_' + Date.now() + '@example.com');"
        ] } },
        { "listen": "test", "script": { "type": "text/javascript", "exec": [
          "pm.test('status 201', () => pm.response.to.have.status(201));",
          "const b = pm.response.json();",
          "pm.test('tem id e email', () => { pm.expect(b).to.have.property('id'); pm.expect(b).to.have.property('email'); });",
          "pm.environment.set('userId', b.id);"
        ] } }
      ],
      "request": {
        "auth": { "type": "noauth" },
        "method": "POST",
        "header": [ { "key": "Content-Type", "value": "application/json" } ],
        "url": { "raw": "{{baseUrl}}/auth/register", "host": ["{{baseUrl}}"], "path": ["auth","register"] },
        "body": { "mode": "raw", "raw": "{\n  \"name\": \"Teste Helfy\",\n  \"email\": \"{{email}}\",\n  \"password\": \"{{password}}\"\n}" }
      }
    },
    {
      "name": "A2 Register duplicado (409)",
      "event": [ { "listen": "test", "script": { "type": "text/javascript", "exec": [
        "pm.test('status 409', () => pm.response.to.have.status(409));"
      ] } } ],
      "request": {
        "auth": { "type": "noauth" },
        "method": "POST",
        "header": [ { "key": "Content-Type", "value": "application/json" } ],
        "url": { "raw": "{{baseUrl}}/auth/register", "host": ["{{baseUrl}}"], "path": ["auth","register"] },
        "body": { "mode": "raw", "raw": "{\n  \"name\": \"Outro\",\n  \"email\": \"{{email}}\",\n  \"password\": \"{{password}}\"\n}" }
      }
    },
    {
      "name": "A3 Login (200)",
      "event": [ { "listen": "test", "script": { "type": "text/javascript", "exec": [
        "pm.test('status 200', () => pm.response.to.have.status(200));",
        "const b = pm.response.json();",
        "pm.test('tem access_token', () => pm.expect(b.access_token).to.be.a('string').and.not.empty);",
        "pm.environment.set('token', b.access_token);"
      ] } } ],
      "request": {
        "auth": { "type": "noauth" },
        "method": "POST",
        "header": [ { "key": "Content-Type", "value": "application/json" } ],
        "url": { "raw": "{{baseUrl}}/auth/login", "host": ["{{baseUrl}}"], "path": ["auth","login"] },
        "body": { "mode": "raw", "raw": "{\n  \"email\": \"{{email}}\",\n  \"password\": \"{{password}}\"\n}" }
      }
    },
    {
      "name": "A4 Login senha errada (401)",
      "event": [ { "listen": "test", "script": { "type": "text/javascript", "exec": [
        "pm.test('status 401', () => pm.response.to.have.status(401));"
      ] } } ],
      "request": {
        "auth": { "type": "noauth" },
        "method": "POST",
        "header": [ { "key": "Content-Type", "value": "application/json" } ],
        "url": { "raw": "{{baseUrl}}/auth/login", "host": ["{{baseUrl}}"], "path": ["auth","login"] },
        "body": { "mode": "raw", "raw": "{\n  \"email\": \"{{email}}\",\n  \"password\": \"senhaErrada\"\n}" }
      }
    },
    {
      "name": "A5 /auth/me sem token (401)",
      "event": [ { "listen": "test", "script": { "type": "text/javascript", "exec": [
        "pm.test('status 401', () => pm.response.to.have.status(401));"
      ] } } ],
      "request": {
        "auth": { "type": "noauth" },
        "method": "GET",
        "url": { "raw": "{{baseUrl}}/auth/me", "host": ["{{baseUrl}}"], "path": ["auth","me"] }
      }
    },
    {
      "name": "A6 PUT perfil (200)",
      "event": [ { "listen": "test", "script": { "type": "text/javascript", "exec": [
        "pm.test('status 200', () => pm.response.to.have.status(200));",
        "const b = pm.response.json();",
        "pm.test('eco do objetivo', () => pm.expect(b.goal).to.eql('EMAGRECER'));",
        "pm.test('eco do peso', () => pm.expect(b.weight_kg).to.eql(80));"
      ] } } ],
      "request": {
        "method": "PUT",
        "header": [ { "key": "Content-Type", "value": "application/json" } ],
        "url": { "raw": "{{baseUrl}}/perfil/{{userId}}", "host": ["{{baseUrl}}"], "path": ["perfil","{{userId}}"] },
        "body": { "mode": "raw", "raw": "{\n  \"age\": 30,\n  \"height_cm\": 170,\n  \"weight_kg\": 80,\n  \"goal\": \"EMAGRECER\",\n  \"diet_type\": \"vegetarian\",\n  \"activity_level\": \"lightly_active\",\n  \"cholesterol\": 210,\n  \"glucose\": 110,\n  \"restrictions\": [\"low_sugar\"],\n  \"preferences\": [\"doces\"],\n  \"allergies\": [\"lactose\"]\n}" }
      }
    },
    {
      "name": "A7 POST alimento manual (201)",
      "event": [ { "listen": "test", "script": { "type": "text/javascript", "exec": [
        "pm.test('status 201', () => pm.response.to.have.status(201));",
        "const b = pm.response.json();",
        "pm.test('source MANUAL', () => pm.expect(b.source).to.eql('MANUAL'));",
        "pm.environment.set('foodId', b.id);"
      ] } } ],
      "request": {
        "method": "POST",
        "header": [ { "key": "Content-Type", "value": "application/json" } ],
        "url": { "raw": "{{baseUrl}}/alimentos", "host": ["{{baseUrl}}"], "path": ["alimentos"] },
        "body": { "mode": "raw", "raw": "{\n  \"name\": \"Banana de Teste\",\n  \"food_group\": \"fruit\",\n  \"nutrition\": { \"energy_kcal_100g\": 89, \"proteins_100g\": 1.1, \"carbohydrates_100g\": 23, \"fat_100g\": 0.3, \"fiber_100g\": 2.6, \"sugar_100g\": 12, \"sodium_mg_100g\": 1 },\n  \"allergen_flags\": [],\n  \"flags\": []\n}" }
      }
    },
    {
      "name": "A8 Add dispensa por alimento_id (201)",
      "event": [ { "listen": "test", "script": { "type": "text/javascript", "exec": [
        "pm.test('status 201', () => pm.response.to.have.status(201));",
        "const b = pm.response.json();",
        "pm.test('food.id == foodId', () => pm.expect(b.food.id).to.eql(pm.environment.get('foodId')));"
      ] } } ],
      "request": {
        "method": "POST",
        "header": [ { "key": "Content-Type", "value": "application/json" } ],
        "url": { "raw": "{{baseUrl}}/dispensa/{{userId}}/adicionar", "host": ["{{baseUrl}}"], "path": ["dispensa","{{userId}}","adicionar"] },
        "body": { "mode": "raw", "raw": "{\n  \"alimento_id\": \"{{foodId}}\",\n  \"quantidade\": 500\n}" }
      }
    },
    {
      "name": "A9 Listar dispensa (200)",
      "event": [ { "listen": "test", "script": { "type": "text/javascript", "exec": [
        "pm.test('status 200', () => pm.response.to.have.status(200));",
        "const b = pm.response.json();",
        "pm.test('contem o alimento adicionado', () => { const ids = b.map(i => i.food.id); pm.expect(ids).to.include(pm.environment.get('foodId')); });"
      ] } } ],
      "request": {
        "method": "GET",
        "url": { "raw": "{{baseUrl}}/dispensa/{{userId}}", "host": ["{{baseUrl}}"], "path": ["dispensa","{{userId}}"] }
      }
    },
    {
      "name": "A10 Score (200)",
      "event": [ { "listen": "test", "script": { "type": "text/javascript", "exec": [
        "pm.test('status 200', () => pm.response.to.have.status(200));",
        "const b = pm.response.json();",
        "pm.test('retorna um score', () => pm.expect(b).to.be.an('array').with.lengthOf(1));",
        "pm.test('score em [0,1]', () => { pm.expect(b[0].score).to.be.at.least(0); pm.expect(b[0].score).to.be.at.most(1); });",
        "pm.test('justificativa nao vazia (SCRUM-19)', () => pm.expect(b[0].justificativa).to.be.a('string').and.not.empty);"
      ] } } ],
      "request": {
        "method": "POST",
        "header": [ { "key": "Content-Type", "value": "application/json" } ],
        "url": { "raw": "{{baseUrl}}/score", "host": ["{{baseUrl}}"], "path": ["score"] },
        "body": { "mode": "raw", "raw": "{\n  \"usuario_id\": \"{{userId}}\",\n  \"alimento_ids\": [\"{{foodId}}\"]\n}" }
      }
    },
    {
      "name": "A11 Receitas sugeridas (200, contrato)",
      "event": [ { "listen": "test", "script": { "type": "text/javascript", "exec": [
        "pm.test('status 200', () => pm.response.to.have.status(200));",
        "const b = pm.response.json();",
        "pm.test('schema receitas/scored', () => { pm.expect(b.receitas).to.be.an('array'); pm.expect(b.scored).to.be.a('boolean'); });"
      ] } } ],
      "request": {
        "method": "GET",
        "url": { "raw": "{{baseUrl}}/receitas/sugeridas/{{userId}}", "host": ["{{baseUrl}}"], "path": ["receitas","sugeridas","{{userId}}"] }
      }
    },
    {
      "name": "A12 Remover da dispensa (204)",
      "event": [ { "listen": "test", "script": { "type": "text/javascript", "exec": [
        "pm.test('status 204', () => pm.response.to.have.status(204));"
      ] } } ],
      "request": {
        "method": "DELETE",
        "url": { "raw": "{{baseUrl}}/dispensa/{{userId}}/{{foodId}}", "host": ["{{baseUrl}}"], "path": ["dispensa","{{userId}}","{{foodId}}"] }
      }
    }
  ]
}
```

- [ ] **Step 2: Validar JSON**

Run: `python3 -c "import json; d=json.load(open('tests/postman/helfy.postman_collection.json')); print(len(d['item']), 'requests')"`
Expected: `12 requests`

- [ ] **Step 3: Commit**

```bash
git add tests/postman/helfy.postman_collection.json
git commit -m "test(postman): collection determinista do fluxo Helfy (12 casos)"
```

---

### Task 6: Executar a automação com newman (verde)

**Files:** nenhum (verificação)

- [ ] **Step 1: Subir o backend**

```bash
docker compose up -d --build
```
Expected: containers `postgres`, `score-engine`, `core-api` up. Aguarde `core-api` saudável.

- [ ] **Step 2: Confirmar a API no ar**

Run: `curl -s http://localhost:8000/health`
Expected: `{"status":"ok"}`

- [ ] **Step 3: Rodar a collection via newman**

Run:
```bash
npx --yes newman run tests/postman/helfy.postman_collection.json \
  -e tests/postman/helfy.postman_environment.json
```
Expected: todas as asserções passam — coluna `failed` = `0` no resumo do newman.

- [ ] **Step 4: Se algo falhar, corrigir a collection/environment e repetir o Step 3**

Investigar o request que falhou (status real vs esperado). Ajustar JSON e reexecutar até `failed = 0`.

- [ ] **Step 5: Derrubar o ambiente (opcional)**

```bash
docker compose down
```

---

### Task 7: README da automação + roteiro do vídeo

**Files:**
- Create: `tests/postman/README.md`

- [ ] **Step 1: Criar o README**

Crie `tests/postman/README.md` com EXATAMENTE este conteúdo:

````markdown
# Automação de Testes — Postman (Sprint 4)

Automação determinística da `core-api` do Helfy: fluxo completo
auth → perfil → dispensa → score → receitas. A collection cria seus próprios
dados (registra um usuário com e-mail único por execução, cria um alimento manual),
então **não depende de seed nem de rede externa** e pode rodar quantas vezes quiser.

## Pré-requisitos

- Backend no ar: na raiz do repositório, `docker compose up -d --build`.
  Confirme com `curl http://localhost:8000/health` → `{"status":"ok"}`.
- Node.js (para `newman`) ou Postman Desktop (para o Collection Runner).

## Rodar via newman (CLI)

```bash
npx --yes newman run tests/postman/helfy.postman_collection.json \
  -e tests/postman/helfy.postman_environment.json
```
Esperado: `failed = 0` no resumo (todas as asserções verdes).

## Rodar via Postman Desktop (Collection Runner)

1. Importar `helfy.postman_collection.json` e `helfy.postman_environment.json`.
2. Selecionar o environment "Helfy Local" no canto superior direito.
3. Abrir a collection → "Run collection" → "Run Helfy Core API — Sprint 4".
4. Observar todos os requests verdes na execução.

## Casos automatizados

| # | Request | Valida |
|---|---|---|
| A1 | POST /auth/register | 201, cria usuário, captura `userId` |
| A2 | POST /auth/register (dup) | 409 e-mail duplicado |
| A3 | POST /auth/login | 200, captura `token` |
| A4 | POST /auth/login (senha errada) | 401 |
| A5 | GET /auth/me sem token | 401 (controle de acesso) |
| A6 | PUT /perfil/{userId} | 200, eco dos campos |
| A7 | POST /alimentos (manual) | 201, captura `foodId` |
| A8 | POST /dispensa/{userId}/adicionar | 201 |
| A9 | GET /dispensa/{userId} | 200, contém o alimento |
| A10 | POST /score | 200, score 0–1 + justificativa (SCRUM-19) |
| A11 | GET /receitas/sugeridas/{userId} | 200, contrato `{receitas[], scored}` |
| A12 | DELETE /dispensa/{userId}/{foodId} | 204 |

> **Nota:** A11 valida o **contrato** do endpoint. A sugestão de receita "real"
> (cobertura ≥70% com alimentos do seed) é coberta pelo teste manual TC-11 no app,
> pois o seed não expõe barcode nem endpoint de listagem — mantendo a automação reprodutível.

## Roteiro do vídeo (entrega Parte B)

1. **Intro (10s):** dizer nome da equipe e que o sistema é API-first (cliente mobile fino).
2. **Configuração (30s):** mostrar `docker compose up -d --build` e `curl http://localhost:8000/health`.
3. **Postman (60s):** abrir o Postman, mostrar a collection importada, o environment "Helfy Local"
   selecionado, e abrir 1–2 requests destacando as abas "Body" e "Tests" (asserções `pm.test`).
4. **Execução (60s):** rodar o Collection Runner e mostrar todos os requests verdes.
5. **CLI (30s):** rodar `npx newman run ...` no terminal e mostrar `failed = 0`.
6. **Fecho (10s):** apontar que o fluxo cobre auth → perfil → dispensa → score → receitas.
````

- [ ] **Step 2: Commit**

```bash
git add tests/postman/README.md
git commit -m "docs(postman): instrucoes de execucao e roteiro do video"
```

---

### Task 8: Apontar artefatos no README raiz e publicar

**Files:**
- Modify: `README.md` (raiz) — seção "Documentação"

- [ ] **Step 1: Adicionar a seção de testes ao README raiz**

No `README.md` da raiz, dentro da seção `## Documentação`, adicione ao final da lista:

```markdown
- Plano de testes (Sprint 4): `docs/testing/2026-06-15-plano-testes-sprint4.md`
- Test Cases para Azure Boards: `tests/manual/azure-boards-testcases.csv`
- Automação Postman: `tests/postman/` (ver `tests/postman/README.md`)
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: aponta artefatos de teste da Sprint 4 no README"
```

- [ ] **Step 3: Publicar a branch develop**

```bash
git push origin develop
```
Expected: push aceito; branch `develop` atualizada no GitHub.

---

### Task 9 (opcional): Sincronizar collection com o Postman cloud via MCP

**Files:** nenhum

- [ ] **Step 1: Criar a collection no Postman cloud (se desejado para compartilhar link)**

Usar a ferramenta MCP `mcp__claude_ai_Postman__createCollection` (ou import manual no Postman
Desktop) a partir de `tests/postman/helfy.postman_collection.json`. Opcional — o arquivo
versionado no repo já é suficiente para a entrega e para o vídeo.

---

## Ações que permanecem manuais do usuário (fora do plano)

- Importar `tests/manual/azure-boards-testcases.csv` no Azure Boards
  (Boards → Work Items → Import from CSV), criar o Test Plan e **adicionar o professor**
  à org/projeto; colar o link na entrega.
- Gravar e publicar o **vídeo** seguindo o roteiro em `tests/postman/README.md`.
- Confirmar visibilidade pública do repo (já confirmado PUBLIC nesta sessão).

---

## Self-Review (preenchido)

**Spec coverage:**
- Parte A — listar testes ✅ (Task 2 §casos + Task 3 CSV) · dados de entrada ✅ · saída esperada ✅ · passos ✅ · Azure Boards ✅ (CSV, Task 3).
- Parte B — ≥4 casos automatizados Postman ✅ (12 casos, Task 5; verificados na Task 6).
- Justificativa Postman ✅ (Task 2, seção dedicada).
- Entrega: branch `develop` ✅ (Tasks 1 e 8) · repo público ✅ · vídeo (roteiro) ✅ (Task 7) · link Azure Boards (ação manual documentada).

**Placeholder scan:** sem TBD/TODO; todo conteúdo de arquivo e comandos estão completos.

**Type/consistency:** nomes de variáveis de ambiente (`email`, `userId`, `token`, `foodId`)
consistentes entre environment (Task 4), pre-request/test scripts e requests (Task 5).
Status codes batem com o contrato real verificado no spec (§2).
