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

### Ferramentas de gravação

| Sistema | Opção gratuita |
|---|---|
| macOS | QuickTime Player → "Nova gravação de tela" |
| Windows | Xbox Game Bar (`Win + G`) ou OBS Studio |
| Linux | OBS Studio ou `SimpleScreenRecorder` |

**Configurações recomendadas:**
- Resolução mínima: 1280 × 720. Prefira 1920 × 1080 se o monitor permitir.
- Frame rate: 30 fps é suficiente.
- Áudio: microfone com narração (sem música de fundo).
- Janela do terminal: fonte ≥ 14 pt, tema escuro (facilita leitura).
- Janela do Postman: maximizada ou em tela cheia.

Grave tudo em uma única tomada contínua (sem cortes) — a maioria das entregas FIAP exige isso.

---

### Cena 1 — Introdução (≈ 10 s)

**O que mostrar:** tela inicial do Postman ou o repositório aberto no VS Code.

**O que falar:**
> "Olá, somos a equipe Helfy. Nosso sistema é API-first: a lógica fica na core-api e o app mobile consome os endpoints. Vou demonstrar a suite de testes automatizados da Sprint 4, que cobre o fluxo completo de auth, perfil, dispensa, score nutricional e receitas."

---

### Cena 2 — Subindo o backend (≈ 30 s)

**O que mostrar:** terminal com os dois comandos abaixo rodando.

```bash
# Na raiz do repositório:
docker compose up -d --build
```

Aguarde até os containers aparecerem como `Started` ou `Running`. Em seguida:

```bash
curl http://localhost:8000/health
# Esperado: {"status":"ok"}
```

**O que falar:**
> "Com um único `docker compose up` temos a core-api na porta 8000, o score-engine na 8001 e o PostgreSQL. O health check confirma que a API está no ar."

**Dica:** se os containers já estiverem rodando de uma sessão anterior, mostre `docker compose ps` primeiro para deixar claro o estado inicial.

---

### Cena 3 — Tour pela collection (≈ 60 s)

**O que mostrar:** Postman Desktop aberto com a collection e o environment importados.

Passo a passo na tela:
1. No painel esquerdo, expanda **Helfy Core API — Sprint 4** e role devagar pelos 12 requests para que fiquem visíveis.
2. Clique no request **A1 — POST /auth/register** e mostre a aba **Body** — destacar o campo `email` com timestamp (`helfy_{{timestamp}}@test.com`) que garante unicidade entre execuções.
3. Clique na aba **Tests** do mesmo request e leia em voz alta uma asserção, por exemplo:
   ```js
   pm.test("status 201", () => pm.response.to.have.status(201));
   pm.test("retorna userId", () => { ... pm.environment.set("userId", ...); });
   ```
4. Repita o passo 3 com **A10 — POST /score**: mostrar que o teste valida `score` entre 0 e 1 e que `justificativa` existe (transparência SCRUM-19).
5. Mostre o environment **Helfy Local** selecionado no canto superior direito e abra-o rapidamente para exibir a variável `baseUrl = http://localhost:8000`.

**O que falar:**
> "Cada request tem asserções na aba Tests. O e-mail usa um timestamp para que a collection possa rodar várias vezes sem conflito. A variável `userId` é capturada no registro e reutilizada nos requests seguintes — o fluxo é encadeado."

---

### Cena 4 — Execução no Collection Runner (≈ 60 s)

**O que mostrar:** execução completa com todos os requests verdes.

Passo a passo:
1. Clique com o botão direito na collection → **Run collection**.
2. Confirme que o environment **Helfy Local** está selecionado e que **todas as 12 requests** estão marcadas.
3. Clique em **Run Helfy Core API — Sprint 4**.
4. Aguarde a execução e mostre o painel de resultado: role devagar pelos 12 requests para que cada um apareça verde.
5. Ao final, destaque o resumo: **"X requests, 0 failures"** (o número exato de asserções aparece ali).

**O que falar:**
> "Todas as asserções passaram: nenhum `failed`. O runner encadeou o token JWT gerado no login e o passou automaticamente nos requests seguintes."

**Dica:** se alguma asserção falhar no ensaio, certifique-se de que o ambiente está limpo (`docker compose down -v && docker compose up -d --build`) antes de gravar.

---

### Cena 5 — Execução via CLI com Newman (≈ 30 s)

**O que mostrar:** terminal rodando o newman e o resumo final.

```bash
npx --yes newman run tests/postman/helfy.postman_collection.json \
  -e tests/postman/helfy.postman_environment.json
```

Deixe o output rolar até aparecer o bloco de resumo. Certifique-se de que a linha **`failed  │  0`** fique visível na tela.

**O que falar:**
> "O mesmo fluxo roda pela linha de comando com Newman — útil para integrar em pipelines de CI. O resultado `failed = 0` confirma que todos os casos passaram."

---

### Cena 6 — Fecho (≈ 10 s)

**O que mostrar:** pode voltar ao Postman com o resultado verde ou mostrar o repositório.

**O que falar:**
> "A suite cobre o fluxo completo: registro, login, configuração de perfil, cadastro de alimento, adição e remoção da dispensa, cálculo de score nutricional personalizado e sugestão de receitas. Obrigado."

---

### Checklist antes de publicar

- [ ] Áudio claro, sem eco ou ruído de fundo excessivo.
- [ ] Todos os 12 requests aparecem verdes na gravação.
- [ ] A linha `failed = 0` do Newman está visível.
- [ ] Nenhuma informação sensível (senhas reais, tokens de produção) aparece na tela.
- [ ] Duração total: entre 3 e 4 minutos.
