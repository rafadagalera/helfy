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
