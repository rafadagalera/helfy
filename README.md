# Helfy

App mobile de alimentação saudável personalizada por IA — FIAP Challenge / CarePlus.

## Estrutura

| Caminho | O que é |
|---|---|
| `apps/mobile/` | App React Native (Expo) — Plano 3 |
| `services/core-api/` | API de produto: auth, perfil, alimentos, dispensa, receitas |
| `services/score-engine/` | Engine de score nutricional (ML, stateless) |
| `docs/` | Specs, planos e documentação técnica |

## Rodando localmente

```bash
docker compose up --build
# score-engine: http://localhost:8001/docs
# core-api:      http://localhost:8000/docs
# postgres:     localhost:5432 (helfy/helfy)
```

## Mobile

```bash
cd apps/mobile && npm install
npx expo start   # escaneie o QR com o app Expo Go
```

**Testes:**
```bash
npm test
```

**Variável de ambiente:** crie `apps/mobile/.env` com:
```
EXPO_PUBLIC_API_URL=http://<seu-ip>:8000
```

## Documentação

- Arquitetura: `docs/superpowers/specs/2026-06-11-helfy-monorepo-design.md`
- Contexto canônico: `CLAUDE.md`
