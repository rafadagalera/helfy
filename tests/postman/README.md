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
