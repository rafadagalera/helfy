# CLAUDE.md — Helfy Project Context

> Este arquivo é o contexto canônico do projeto Helfy para agentes de execução (Claude Code, antigravity, etc.).
> Ele descreve arquitetura, domínio, épicos, tasks, dependências e convenções de código.
> **Leia este arquivo inteiro antes de planejar ou executar qualquer tarefa.**

---

## 1. Visão Geral do Produto

**Helfy** é um app mobile de alimentação saudável personalizada por IA, desenvolvido como FIAP Challenge para a **CarePlus** (parceira HealthTech).

### Problema que resolve
A maioria dos apps de receitas ignora o perfil de saúde individual do usuário. Para operadoras de saúde, isso representa baixo engajamento preventivo e sinistralidade elevada em doenças crônicas.

### Solução
Um app que conecta o que o usuário **tem na dispensa** com receitas personalizadas pelo seu **perfil de saúde**, usando um score nutricional gerado por ML.

### Fluxo principal
```
Usuário cadastra perfil (preferências, restrições, dados de saúde, objetivo)
    ↓
Scanneia itens da despensa via barcode → monta "dispensa digital"
    ↓
Engine de score nutricional (ML) gera score por par [usuário × alimento]
    ↓
Serviço determinístico cruza dispensa + scores + receitas pré-cadastradas
    ↓
App exibe receitas personalizadas viáveis com o que o usuário já tem em casa
```

---

## 2. Stack Técnica

| Camada | Tecnologia |
|---|---|
| Mobile | React Native via Expo (iOS + Android) |
| Backend | Python/FastAPI — `core-api` modular por domínio |
| AI/ML | API isolada (`score-engine`) — modelo de score nutricional por par usuário × alimento |
| Receitas | Serviço determinístico com receitas pré-cadastradas (módulo da core-api) |
| Banco | PostgreSQL (SQLAlchemy 2 + Alembic) |
| Barcode | Open Food Facts (SCRUM-14) |

### Princípios de arquitetura
- A **API de IA é isolada e stateless** — pode ser evoluída sem quebrar o produto
- O **serviço de receitas é determinístico** — garante reprodutibilidade e auditabilidade
- Os domínios são desacoplados: perfil, dispensa, receitas, score

> Arquitetura detalhada: `docs/superpowers/specs/2026-06-11-helfy-monorepo-design.md`

---

## 3. Estrutura de Épicos e Tasks (Sprint 1)

Projeto Jira: `dagalera.atlassian.net` — projeto `SCRUM`

### SCRUM-7 — Perfil do Usuário
Gerencia o cadastro, onboarding e configurações de perfil do usuário.

| Task | Título | Prioridade | Depende de |
|---|---|---|---|
| SCRUM-12 | Cadastro de usuário | Highest | — |
| SCRUM-13 | Configurações de perfil | High | SCRUM-12 |
| SCRUM-27 | Tela de onboarding | High | SCRUM-12 |
| SCRUM-28 | Tela de perfil | Medium | SCRUM-13 |

**Dados coletados no perfil:**
- Preferências e restrições dietárias
- Altura, peso
- Dados de saúde: colesterol, glicose
- Objetivo: emagrecer / ganhar massa / manter-se saudável

---

### SCRUM-8 — Input de Produtos
Permite ao usuário adicionar produtos à sua dispensa digital via scan ou input manual.

| Task | Título | Prioridade | Depende de |
|---|---|---|---|
| SCRUM-14 | Base de produtos | Highest | — |
| SCRUM-15 | Input manual | Medium | SCRUM-14 |
| SCRUM-16 | Scan de Infos Nutricionais | High | SCRUM-14 |
| SCRUM-29 | Tela de cadastro de produtos | Medium | SCRUM-15, SCRUM-16 |

**Observações:**
- SCRUM-14 é gargalo crítico — sem a base de produtos, nenhuma outra task de input funciona
- O scan deve ler o barcode e buscar os dados nutricionais na base

---

### SCRUM-9 — Engine de Score Nutricional
Core de IA do produto. Modelo ML que gera score personalizado por par usuário × alimento.

| Task | Título | Prioridade | Depende de |
|---|---|---|---|
| SCRUM-17 | Definir regras da engine | Highest | SCRUM-7 (perfil definido) |
| SCRUM-18 | API de score | Highest | SCRUM-17 |
| SCRUM-19 | Transparência de resultado | Low | SCRUM-18 |

**Observações:**
- O modelo considera: restrições, preferências, objetivo e marcadores de saúde do usuário
- A API pública recebe `{ usuario_id, alimento_ids: [] }` (na core-api) e retorna `[{ alimento_id, score: float 0–1, justificativa? }]`
- A engine em si é stateless: recebe perfil + alimentos no request
- SCRUM-19 (transparência) é o "explainability" — mostrar ao usuário *por que* um alimento tem aquele score

---

### SCRUM-10 — Dispensa Digital
CRUD da dispensa do usuário — lista de alimentos que ele tem em casa.

| Task | Título | Prioridade | Depende de |
|---|---|---|---|
| SCRUM-21 | Construir API da dispensa | High | SCRUM-14 |
| SCRUM-26 | Tela da dispensa | Medium | SCRUM-21 |

---

### SCRUM-11 — Receitas
Serviço que combina dispensa + scores e retorna receitas viáveis.

| Task | Título | Prioridade | Depende de |
|---|---|---|---|
| SCRUM-24 | Integração com APIs | High | SCRUM-18, SCRUM-21 |

**Observações:**
- O serviço é **determinístico** — dado o mesmo input, sempre retorna o mesmo output
- Lógica: seleciona alimentos da dispensa com maior score → busca receitas pré-cadastradas que os utilizem
- Receitas pré-cadastradas devem ser populadas no banco antes desta task (seed)

---

### SCRUM-22 — App Mobile
Setup e infraestrutura base do app React Native.

| Task | Título | Prioridade | Depende de |
|---|---|---|---|
| SCRUM-23 | Setup do App | Highest | — |
| SCRUM-20 | Modelo do banco | Highest | SCRUM-7, SCRUM-8 (domínios definidos) |

**Observações:**
- SCRUM-23 deve ser a **primeira task executada** — sem o setup, nenhuma tela pode ser desenvolvida
- SCRUM-20 define o schema do banco relacional; deve cobrir todas as entidades: usuário, perfil, alimento, dispensa, receita, score

---

## 4. Grafo de Dependências

```
SCRUM-23 (Setup App)
    └─→ [todas as telas]

SCRUM-14 (Base de Produtos)
    ├─→ SCRUM-15 (Input manual)
    ├─→ SCRUM-16 (Scan barcode)
    └─→ SCRUM-21 (API da dispensa)

SCRUM-12 (Cadastro de usuário)
    ├─→ SCRUM-13 (Config. perfil)
    └─→ SCRUM-27 (Tela onboarding)

SCRUM-17 (Regras da engine) — depende de perfil estar definido
    └─→ SCRUM-18 (API de score)
            └─→ SCRUM-19 (Transparência)
            └─→ SCRUM-24 (Integração receitas) ←── SCRUM-21 (API dispensa)

SCRUM-20 (Modelo do banco) — deve preceder qualquer persistência
```

**Tasks que podem rodar em paralelo (sem dependência entre si):**
- SCRUM-23 + SCRUM-12 + SCRUM-14
- SCRUM-15 + SCRUM-16 (após SCRUM-14)
- SCRUM-13 + SCRUM-27 (após SCRUM-12)

---

## 5. Entidades de Domínio

```
Usuario
  ├── id
  ├── email, senha (auth)
  ├── nome, altura, peso
  ├── objetivo: enum(EMAGRECER, GANHAR_MASSA, MANTER)
  ├── restricoes: string[] (ex: lactose, gluten, vegano)
  ├── preferencias: string[]
  └── dados_saude: { colesterol, glicose }

Alimento
  ├── id
  ├── nome
  ├── codigo_barras
  └── info_nutricional: { calorias, proteinas, carboidratos, gorduras, fibras, ... }

Dispensa
  ├── usuario_id
  ├── alimento_id
  └── quantidade (opcional)

ScoreNutricional
  ├── usuario_id
  ├── alimento_id
  ├── score: float (0.0 – 1.0)
  └── justificativa?: string

Receita
  ├── id
  ├── nome
  ├── ingredientes: Alimento[]
  ├── modo_preparo
  └── info_nutricional_total
```

---

## 6. Contratos de API (esperados)

### Auth / Perfil
```
POST   /auth/register        → cria usuário
POST   /auth/login           → retorna JWT
GET    /perfil/{id}          → retorna perfil
PUT    /perfil/{id}          → atualiza perfil
```

### Dispensa
```
GET    /dispensa/{usuario_id}              → lista alimentos da dispensa
POST   /dispensa/{usuario_id}/adicionar   → adiciona alimento por barcode ou id
DELETE /dispensa/{usuario_id}/{alimento_id}
```

### Score
```
POST   /score
  body: { usuario_id, alimento_ids: [] }
  response: [{ alimento_id, score, justificativa? }]
```

### Receitas
```
GET    /receitas/sugeridas/{usuario_id}
  → internamente: busca dispensa → calcula scores → retorna top receitas viáveis
```

### Alimentos
```
GET    /alimentos/barcode/{codigo}   → busca por código de barras
GET    /alimentos/{id}
```

---

## 7. Convenções e Decisões de Projeto

- **Idioma do código:** inglês (variáveis, métodos, classes). Comentários e commits em português.
- **O score é calculado server-side** — nunca no cliente. O app consome o score via API.
- **Receitas são pré-cadastradas** — não são geradas por IA. O serviço é determinístico por design.
- **Barcode scan** usa Open Food Facts como base de produtos externa (SCRUM-14).
- **Autenticação** via JWT. O token deve ser passado em todas as requisições autenticadas via `Authorization: Bearer <token>`.
- **A API de score é isolada** e pode ser substituída/evoluída sem impacto no restante do sistema.

---

## 8. Roadmap Pós-MVP

1. Notificações inteligentes e plano semanal de refeições
2. Integração com nutricionistas da rede CarePlus
3. Lista de compras inteligente com base nos scores
4. Parceria com marketplaces (compra in-app)
5. Telemetria de saúde para programas preventivos da operadora

---

## 9. Contexto de Negócio (CarePlus)

O produto foi proposto pela **CarePlus** como solução de engajamento preventivo de beneficiários. O valor esperado pela operadora:
- Engajamento diário do beneficiário via alimentação
- Dados de saúde atualizados continuamente
- Redução de sinistralidade em doenças crônicas (hipertensão, diabetes, obesidade)
- Diferencial competitivo na proposta de valor da operadora

---

*Gerado com base no histórico de sessões de planejamento do projeto Helfy (FIAP Challenge 2026).*
