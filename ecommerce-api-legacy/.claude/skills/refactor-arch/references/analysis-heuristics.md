# Heurísticas de Análise — Fase 1

Este documento define **como** detectar a stack e mapear a arquitetura de qualquer projeto. Use cada seção como uma checklist; não pule etapas.

---

## 1. Detecção de linguagem

Aplique em ordem (a primeira que casar vence):

1. **Manifesto presente** (mais confiável):
   - `package.json` ou `package-lock.json` → **Node.js / JavaScript** (TypeScript se houver `tsconfig.json` ou arquivos `.ts`).
   - `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` → **Python**.
   - `pom.xml`, `build.gradle`, `build.gradle.kts` → **Java/Kotlin**.
   - `composer.json` → **PHP**.
   - `Gemfile` → **Ruby**.
   - `go.mod` → **Go**.
   - `Cargo.toml` → **Rust**.
2. **Distribuição de extensões** (fallback) com `Glob`:
   - `**/*.py` >= 3 arquivos → Python.
   - `**/*.js` ou `**/*.ts` >= 3 arquivos → Node.
   - etc.

Se mais de uma stack aparece (ex: Python + JS), eleja a stack do **arquivo de entry-point** (procure `main`, `app.py`, `app.js`, `index.js`, `server.py`, etc.).

---

## 2. Detecção de framework

Estratégia em duas etapas:

### a) Ler o manifesto

- **Python (`requirements.txt`):** procurar `flask`, `django`, `fastapi`, `bottle`, `tornado`. Capturar a versão (ex: `flask==3.1.1`).
- **Node (`package.json`):** ler `dependencies` e `devDependencies`. Procurar `express`, `koa`, `fastify`, `nestjs`, `hapi`, `@nestjs/core`. Capturar versão.
- **Java:** procurar `spring-boot`, `quarkus`, `micronaut` no `pom.xml`/`build.gradle`.

### b) Confirmar pelo código (caso o manifesto seja ambíguo ou inexistente)

`Grep` por imports/requires:

| Padrão | Framework |
|---|---|
| `from flask import` | Flask (Python) |
| `from django` | Django (Python) |
| `from fastapi import` | FastAPI (Python) |
| `require('express')` ou `from 'express'` | Express (Node) |
| `require('koa')` | Koa (Node) |
| `from '@nestjs/` | NestJS (Node) |
| `import org.springframework` | Spring (Java) |

Se nenhum framework é detectado: registre `Framework: vanilla <linguagem>` e ainda assim aplique MVC genérico.

---

## 3. Detecção de banco de dados

`Grep` no código (qualquer linguagem):

| Padrão | Banco |
|---|---|
| `sqlite3`, `sqlite:///`, `:memory:`, `.db` em conexão | SQLite |
| `psycopg`, `pg`, `postgres://`, `pg-promise` | PostgreSQL |
| `mysql`, `mysql2`, `pymysql`, `mysql://` | MySQL |
| `mongoose`, `pymongo`, `mongodb://` | MongoDB |
| `redis`, `ioredis` | Redis (cache, normalmente complementar) |
| `SQLAlchemy`, `prisma`, `sequelize`, `typeorm` | ORM (anote — afeta a Fase 3) |

### Listagem de tabelas/coleções

- Se houver `CREATE TABLE` no código (SQL puro): extrair nomes via regex `CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)`.
- Se houver ORM (SQLAlchemy/Prisma/Sequelize): listar classes `db.Model` (Python) ou `model X` (Prisma) ou `define('X', ...)` (Sequelize).

---

## 4. Detecção do domínio

Inferir o **propósito** do projeto agrupando nomes de tabelas, models e rotas:

- Tabelas: `produtos`, `pedidos`, `usuarios`, `itens_pedido` → **e-commerce**.
- Tabelas: `courses`, `enrollments`, `payments`, `users` → **LMS / educação**.
- Tabelas: `tasks`, `users`, `categories` → **task / project management**.
- Tabelas: `posts`, `comments`, `users` → **blog / social**.
- Tabelas: `appointments`, `patients`, `doctors` → **health**.

A frase de saída deve ser objetiva: `Domain: E-commerce API (produtos, pedidos, usuários)` — em uma linha.

---

## 5. Mapeamento de arquitetura

Classifique em **uma** das três categorias (essa classificação dirige o escopo da Fase 3):

### `monolithic-flat`
- ≤ 6 arquivos de código no nível raiz, sem subpastas relevantes.
- Misturando rotas, models, queries e validação no mesmo arquivo.
- **Exemplo:** `code-smells-project/` (4 arquivos `.py` na raiz).
- **Ação na Fase 3:** criar `src/` do zero.

### `partially-layered`
- Já existe alguma estrutura por camada (`models/`, `routes/`, `services/`, `utils/`), porém:
  - rotas contêm lógica de negócio,
  - modelos misturam persistência + apresentação,
  - falta `config/`, `controllers/` ou `middlewares/`.
- **Exemplo:** `task-manager-api/` (`models/`, `routes/`, `services/`, `utils/` mas sem `controllers/`, `config/`).
- **Ação na Fase 3:** **promover estrutura para `src/`** completo, preservando nomes de blueprints/rotas para não quebrar a API.

### `layered`
- Estrutura `src/{config,models,views,controllers,services,middlewares}` ou equivalente já existe.
- Camadas separadas e respeitadas.
- **Ação na Fase 3:** focar só em correções pontuais (segurança, deprecated APIs, N+1).

### Sinal de god file/class (independente da categoria)
- Qualquer arquivo `.py`/`.js` com > 300 LOC contendo `def`/`function` para múltiplos domínios não-relacionados → flag separada na Fase 2 (mesmo que o projeto seja `partially-layered`).

---

## 6. Comando de execução

Detectar como o projeto sobe:

| Manifesto | Heurística |
|---|---|
| `package.json` com `scripts.start` | `npm start` |
| `package.json` sem `start` | `node <main do package.json>` |
| `requirements.txt` + `app.py` na raiz | `python app.py` |
| `pyproject.toml` com `[tool.poetry.scripts]` | usar o script |
| `Procfile` | usar a primeira linha `web:` |
| `Dockerfile` com `CMD` | usar o `CMD` |

**Importante:** se houver script de seed obrigatório (procure `seed.py`, `seed.js`, ou `npm run seed`), registre-o como pré-requisito do `Run command`. Exemplo do desafio: `task-manager-api` requer `python seed.py && python app.py`.

Se nenhuma heurística casar: imprimir `Run command: <não detectado — solicitar ao usuário>` e perguntar.

---

## 7. Contagem de arquivos e LOC

- `Glob` por extensões da stack detectada (`**/*.py`, `**/*.js`, etc.), excluindo `node_modules/`, `__pycache__/`, `.venv/`, `dist/`, `build/`.
- Para LOC aproximado: `wc -l` no resultado (Bash). Não precisa ser exato — arredondar para a centena.

---

## 8. Saída final da Fase 1

Renderize **exatamente** este bloco (preencha cada campo):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:       <linguagem>
Framework:      <framework + versão>
Dependencies:   <lista relevante, separada por vírgula>
Domain:         <domínio inferido em 1 linha>
Architecture:   <monolithic-flat | partially-layered | layered> — <descrição>
Source files:   <N> files analyzed (~<L> LOC)
DB tables:      <lista, separada por vírgula>
Run command:    <comando — incluir seed se obrigatório>
================================
```

Sem isso, a Fase 2 não tem contexto. **Não pule.**
