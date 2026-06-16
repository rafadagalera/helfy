# Spec — Plano de Testes e Automação (Sprint 4)

> **Status:** aprovado em brainstorming · **Data:** 2026-06-15
> **Projeto:** Helfy (FIAP Challenge / CarePlus)
> **Entregável:** Sprint 4 — testes manuais (Azure Boards) + automação (Postman)

---

## 1. Objetivo

Atender, item a item, ao enunciado da Sprint 4:

- **PARTE A** — Plano de testes **manuais**, de validação a **nível de sistema**, cobrindo as
  funcionalidades principais, registrado no **Azure Boards**. Cada caso precisa ter:
  (1) teste listado, (2) dados de entrada, (3) dados de saída esperada, (4) procedimento/passos.
  Dados **controlados e predefinidos** (sem placeholders).
- **PARTE B** — Pelo menos **4 casos de teste automatizados** validando o sistema, usando
  **Postman** (sistema é API-first; ver justificativa em §6).
- **ENTREGA** — Repositório GitHub **público**, branch **`develop`**, com link do Azure Boards
  (professor como membro da org/projeto) e link de **vídeo** mostrando configuração e execução
  da automação.

### Não-objetivos (YAGNI)

- Não criar testes de UI automatizados (decisão registrada em §6 — Postman + justificativa).
- Não cobrir endpoints administrativos/internos que não fazem parte do fluxo de usuário.
- Não recriar os testes unitários já existentes (`pytest` na core-api / score-engine, `jest` no mobile).

---

## 2. Sistema sob teste (contrato real verificado)

API: `services/core-api` (FastAPI). Endpoints confirmados no código:

| Fluxo | Método + rota | Notas de contrato |
|---|---|---|
| Registro | `POST /auth/register` | `{email, password(≥8), name}` → 201 `{id, email, name}`; **409** se e-mail repetido |
| Login | `POST /auth/login` | `{email, password}` → 200 `{access_token, token_type}`; **401** se inválido |
| Usuário atual | `GET /auth/me` | Bearer token → 200 `{id, email, name}`; **401** sem token |
| Perfil (upsert) | `PUT /perfil/{usuario_id}` | exige `age(18–110), height_cm(100–250), weight_kg(30–300), goal`; opcionais `diet_type, activity_level, cholesterol, glucose, restrictions[], preferences[], allergies[]` |
| Perfil (ler) | `GET /perfil/{usuario_id}` | **404** se ainda não cadastrado |
| Alimento manual | `POST /alimentos` | `{name, food_group, nutrition{}, allergen_flags[], flags[]}` → 201 (`source: MANUAL`) |
| Alimento por id | `GET /alimentos/{id}` | **404** se inexistente |
| Alimento por barcode | `GET /alimentos/barcode/{codigo}` | Open Food Facts; **404**/**502** — **não determinístico** |
| Dispensa add | `POST /dispensa/{usuario_id}/adicionar` | `alimento_id` **OU** `codigo_barras` (exatamente um) → 201 |
| Dispensa listar | `GET /dispensa/{usuario_id}` | 200 lista ordenada por nome |
| Dispensa remover | `DELETE /dispensa/{usuario_id}/{alimento_id}` | 204; **404** se item ausente |
| Score | `POST /score` | `{usuario_id, alimento_ids[≥1]}` → 200 `[{alimento_id, score(0–1), justificativa}]`; **409** sem perfil; **404** alimento inexistente; **503** engine off |
| Receitas | `GET /receitas/sugeridas/{usuario_id}` | 200 `{receitas[], scored:bool}`; cobertura ≥70%; **409** sem perfil |

**Autorização:** todas as rotas (exceto register/login) exigem `Authorization: Bearer <JWT>`.
`require_owner` garante que `usuario_id` na rota = usuário do token (403 caso contrário).

**Enums relevantes (valores controlados para os testes):**
- `goal`: `EMAGRECER | GANHAR_MASSA | MANTER`
- `diet_type`: `omnivore | vegetarian | vegan | keto | pescatarian | paleo`
- `restrictions`: `low_sodium | low_sugar | low_fat | high_protein | low_carb`
- `allergies`/`allergen_flags`: `gluten | lactose | nuts | shellfish | eggs | soy`
- `flags` (alimento): `animal_product | meat | fish`

---

## 3. Estratégia: manual = UI/sistema, automação = API

Separação deliberada para cobrir as duas camadas do produto sem redundância:

- **Parte A (manual)** é executada por um humano **contra o sistema rodando** — o app mobile
  (Expo) para fluxos com tela, e o Swagger UI (`/docs`) para validação direta de back-end quando
  não houver tela equivalente. Inclui os fluxos **não determinísticos** (scan de barcode via Open
  Food Facts; sugestão de receita "real" com dados do seed) que não cabem numa automação estável.
- **Parte B (automação Postman)** valida o **contrato e a lógica de negócio da API** por um caminho
  **100% determinístico e self-contained** (cria seus próprios dados, não depende de seed nem de
  rede externa).

---

## 4. PARTE A — Plano de testes manuais

~12 casos cobrindo os 5 fluxos principais (caminho feliz + negativos-chave). Cada caso tem:
**ID, título, pré-condições, dados de entrada (predefinidos), saída esperada (concreta), passos numerados.**

| ID | Fluxo | Caso | Tipo |
|---|---|---|---|
| TC-01 | Auth | Registro de novo usuário | feliz |
| TC-02 | Auth | Registro com e-mail já existente → erro | negativo |
| TC-03 | Auth | Login com credenciais válidas (recebe token) | feliz |
| TC-04 | Auth | Login com senha incorreta → erro | negativo |
| TC-05 | Perfil | Completar onboarding/perfil (objetivo, dados de saúde) | feliz |
| TC-06 | Perfil | Salvar perfil com peso fora do intervalo → validação | negativo |
| TC-07 | Dispensa | Adicionar alimento por **scan de barcode** (Open Food Facts) | feliz |
| TC-08 | Dispensa | Adicionar alimento por **input manual** | feliz |
| TC-09 | Dispensa | Remover alimento da dispensa | feliz |
| TC-10 | Score | Ver score nutricional + **justificativa** de um alimento (transparência) | feliz |
| TC-11 | Receitas | Ver **receitas sugeridas** viáveis com a dispensa | feliz |
| TC-12 | Receitas | Pedir sugestões **sem perfil cadastrado** → bloqueio | negativo |

Exemplo de formato de caso (será replicado para todos):

> **TC-03 — Login com credenciais válidas**
> **Pré-condições:** usuário `teste.helfy@example.com` / `Senha@12345` já registrado (TC-01).
> **Dados de entrada:** email=`teste.helfy@example.com`, senha=`Senha@12345`.
> **Saída esperada:** tela inicial (home) carrega; sessão autenticada; token JWT armazenado.
> **Passos:** 1) Abrir o app. 2) Tela de login. 3) Preencher e-mail e senha. 4) Tocar "Entrar".
> 5) Verificar redirecionamento para a Home com receitas sugeridas.

### Entrega no Azure Boards

- Gerar `tests/manual/azure-boards-testcases.csv` — Test Case **work items** importáveis via
  **Boards → Work Items → Import from CSV** no Azure DevOps.
- Colunas: `Work Item Type` (= `Test Case`), `Title`, `Test Step` / `Step Action` /
  `Step Expected`, `Tags`, mais um campo de descrição com pré-condições e dados de entrada.
  *Observação técnica:* o campo nativo de steps (`Microsoft.VSTS.TCM.Steps`) é XML; o CSV cria os
  work items e os passos vão num formato legível. O doc Markdown é a fonte de verdade humana; o CSV
  acelera a carga.
- **Ações manuais do usuário** (fora do alcance do agente): subir o CSV, criar o Test Plan,
  adicionar o professor como membro da org/projeto, e colar o link na entrega.

---

## 5. PARTE B — Automação Postman (≥4 casos)

Collection única, **encadeada**, que cria seus próprios dados — sem dependência de seed ou rede:

1. **Setup/login** — `POST /auth/register` (ou ignora 409) → `POST /auth/login`, salva
   `{{token}}` e `{{userId}}` em variáveis de ambiente.
2. Requests seguintes reusam `{{token}}` no header e os ids capturados.

Casos automatizados (cada um com asserções `pm.test`) — **muito além do mínimo de 4**:

| # | Request | Asserções principais |
|---|---|---|
| A1 | `POST /auth/register` | 201; body tem `id`, `email`; salva `userId` |
| A2 | `POST /auth/register` (mesmo e-mail) | **409**; mensagem de e-mail já cadastrado |
| A3 | `POST /auth/login` | 200; `access_token` presente; salva `token` |
| A4 | `POST /auth/login` (senha errada) | **401** |
| A5 | `GET /auth/me` **sem token** | **401** (controle de acesso) |
| A6 | `PUT /perfil/{{userId}}` | 200; eco dos campos (goal, height, weight) |
| A7 | `POST /alimentos` (manual, determinístico) | 201; `source=MANUAL`; salva `foodId` |
| A8 | `POST /dispensa/{{userId}}/adicionar` (por `alimento_id`) | 201; `food.id == foodId` |
| A9 | `GET /dispensa/{{userId}}` | 200; lista contém `foodId` |
| A10 | `POST /score` | 200; `score` ∈ [0,1]; `justificativa` não vazia (SCRUM-19) |
| A11 | `GET /receitas/sugeridas/{{userId}}` | 200; schema `{receitas[], scored:bool}` válido |
| A12 | `DELETE /dispensa/{{userId}}/{{foodId}}` | 204 |

> **Nota de determinismo registrada no README:** A11 valida o **contrato** do endpoint de receitas.
> A sugestão de receita "real" (com cobertura ≥70%) depende dos alimentos do **seed**, que não têm
> barcode nem endpoint de listagem — por isso esse cenário é coberto como **teste manual (TC-11)**
> no app, não na automação. Decisão consciente para manter o run reprodutível.

### Artefatos e execução

```
tests/postman/
  helfy.postman_collection.json     # collection com os requests + pm.test
  helfy.postman_environment.json    # baseUrl, credenciais de teste, vars (token, userId, foodId)
  README.md                         # como rodar + roteiro do vídeo
```

- Construída via Postman MCP e **exportada para o repo** (versionada, não só na nuvem).
- Execução: **Collection Runner** (para gravar o vídeo) **e** `newman` (CLI, reprodutível):
  `newman run helfy.postman_collection.json -e helfy.postman_environment.json`.
- Pré-requisito do run: `docker compose up` (core-api em `http://localhost:8000`).

---

## 6. Decisão registrada — Postman apesar de existir UI

O enunciado diz "Selenium/Katalon **se** tiver telas; **se for só APIs**, Postman". O Helfy tem app
mobile, então não é "só APIs". **Decisão (aprovada pelo usuário):** usar Postman + **justificativa
explícita no plano de testes**:

> O app mobile é um **cliente fino** — toda a lógica de negócio, validação, score e regras de
> receita reside na `core-api`. Automatizar a API exercita o núcleo do sistema de ponta a ponta.
> A camada de UI é validada manualmente (Parte A) contra o app real.

Risco residual de penalidade: baixo, mitigado pela justificativa. Alternativa descartada por
custo/benefício: 1–2 casos Selenium no Expo Web (mais setup e 2º vídeo).

---

## 7. Mecânica de entrega

1. Criar branch **`develop`** a partir de `main`; push de todos os artefatos.
2. Repo `rafadagalera/helfy` já confirmado **público**.
3. **CSV** + instruções de import no Azure Boards (ação de upload é do usuário).
4. **Roteiro de vídeo** em `tests/postman/README.md`: subir ambiente (`docker compose up`),
   abrir Postman, importar collection+environment, rodar o Collection Runner mostrando todos os
   testes verdes, e o equivalente em `newman` no terminal.

### Ações que permanecem manuais do usuário

- Subir o CSV no Azure Boards e adicionar o professor à org/projeto; colar o link.
- Gravar e publicar o vídeo seguindo o roteiro.

---

## 8. Critérios de aceite

- [ ] Plano de testes manuais em Markdown com 12 casos, cada um com os 4 itens pontuados, dados predefinidos.
- [ ] CSV importável de Test Cases no Azure Boards.
- [ ] Collection Postman com ≥4 (entregamos ~12) casos com asserções, encadeada e determinística.
- [ ] Environment Postman versionado.
- [ ] README com instruções de execução (Runner + newman) e roteiro do vídeo.
- [ ] Branch `develop` publicada com todos os artefatos.
- [ ] `newman run` passa 100% verde contra a core-api local.
