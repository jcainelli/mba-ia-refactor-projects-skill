# Catálogo de Anti-Patterns — Fase 2

Este catálogo é a **fonte canônica** dos problemas que a skill detecta. Cada entrada tem `id`, `severity`, `signals` (heurísticas de detecção que você aplica via `Grep`/`Glob`) e `recommendation`.

**Regras:**
- Severidade segue o critério do desafio: `CRITICAL` > `HIGH` > `MEDIUM` > `LOW`.
- Sempre inclua o `id` no relatório para que o `refactoring-playbook.md` possa ser cruzado.
- Cada finding precisa de **arquivo e linha exatos** — sem isso, descarte ou peça reverificação.

---

## CRITICAL

### `SQL_INJECTION_STRING_CONCAT`
- **MVC violation:** Models executando SQL não-parametrizado.
- **Signals:**
  - Python: `cursor.execute("..." + str(...))`, `cursor.execute(f"... {var}")`, `cursor.execute("..." % ...)`.
  - Node: `db.run(\`... ${var}\`)`, `db.all("..." + var)`.
- **Impact:** Permite injeção arbitrária de SQL — vetor de ataque CVE-equivalente.
- **Recommendation:** Substituir por placeholders (`?` em Python sqlite3 / Node sqlite3, `:name` em SQLAlchemy, `$1` em pg). Ver playbook §4.

### `HARDCODED_SECRET`
- **MVC violation:** Configuração em código (deveria estar em `config/` lendo de env).
- **Signals:** `Grep` por:
  - `SECRET_KEY\s*=\s*["']`, `SECRET\s*=\s*["']`,
  - `password\s*=\s*["']`, `pass\s*=\s*["']`,
  - `api[_-]?key\s*=\s*["']`, `gateway[_-]?key`,
  - `pk_live_`, `sk_live_`, `Bearer [A-Za-z0-9_\-]+`,
  - `smtp.*password`, `smtp_pass`.
- **Impact:** Credenciais commitadas no repo expõem produção. Rotacionar é caro.
- **Recommendation:** Mover para `.env` (gitignored) e ler via `os.environ` / `process.env`. Ver playbook §1.

### `PLAINTEXT_PASSWORD`
- **MVC violation:** Modelo armazenando dado sensível sem hash.
- **Signals:**
  - Schema com `senha TEXT` ou `password TEXT/VARCHAR` sem `_hash` no nome.
  - INSERTs gravando o valor cru sem chamar nenhuma função de hash.
  - Login comparando `WHERE senha = '<input>'` literal.
- **Impact:** Vazamento de DB = vazamento de credenciais reais; CWE-256.
- **Recommendation:** `bcrypt`/`argon2`/`scrypt`. Ver playbook §5.

### `WEAK_HASH_FOR_AUTH`
- **MVC violation:** Modelo usando algoritmo fraco para senha.
- **Signals:**
  - Python: `hashlib.md5(...)` ou `hashlib.sha1(...)` em fluxo de senha; `import hashlib` + uso em `set_password`/`check_password`.
  - Node: `crypto.createHash('md5')` ou `'sha1'` em fluxo de senha.
  - Funções caseiras (ex: `badCrypto`, `simpleHash`) — qualquer hash não consagrado.
- **Impact:** MD5/SHA1 quebrados há mais de uma década; rainbow tables existem.
- **Recommendation:** `bcrypt`/`argon2`. Ver playbook §5.

### `ARBITRARY_SQL_ENDPOINT`
- **MVC violation:** Roteamento aceitando SQL cru do cliente.
- **Signals:** Endpoint que recebe um campo `query`/`sql`/`q` e o passa direto para `cursor.execute` ou `db.run` sem validação.
- **Impact:** Equivalente a dar acesso shell ao banco — qualquer atacante autenticado pode dropar tabelas.
- **Recommendation:** Remover o endpoint. Se admin precisa rodar queries, expor endpoints específicos com schema fechado.

### `PII_LEAK_IN_RESPONSE`
- **MVC violation:** Serializer/View vazando campos sensíveis.
- **Signals:**
  - `to_dict()` ou serializer que inclui `password`, `senha`, `password_hash`, `secret`, `token`, `api_key` no payload de resposta.
  - Endpoints administrativos retornando objetos completos sem allow-list de campos.
- **Impact:** Vazamento direto via API — qualquer cliente autenticado obtém o hash da senha.
- **Recommendation:** Allow-list de campos seguros no serializer. Ver playbook §10.

---

## HIGH

### `GOD_FILE_OR_CLASS`
- **MVC violation:** Mistura de responsabilidades em um só arquivo/classe.
- **Signals:**
  - Arquivo > 300 LOC contendo (a) rotas + (b) queries SQL + (c) validações + (d) lógica de negócio.
  - Em Node: classe única que faz schema do DB + roteamento + payment + audit.
- **Impact:** Impossível testar em isolamento; qualquer mudança propaga.
- **Recommendation:** Quebrar por entidade/domínio em `models/`, `controllers/`, `views/`. Ver playbook §2.

### `BUSINESS_LOGIC_IN_VIEW`
- **MVC violation:** Camada de View carregando regras de negócio.
- **Signals:**
  - Handler de rota com `if status not in [...]`, validação de range, cálculo de desconto, regras condicionais.
  - Controller chamando vários models e orquestrando fluxo dentro do handler de rota (em vez de em uma camada `controllers/` ou `services/`).
- **Impact:** Lógica não-reutilizável, difícil de testar sem subir HTTP.
- **Recommendation:** Extrair para `controllers/` ou `services/`. Ver playbook §3.

### `CALLBACK_HELL`
- **MVC violation:** Controller ilegível por aninhamento profundo.
- **Signals (Node):** ≥ 3 níveis de callbacks aninhados, especialmente com `db.all`/`db.get`/`db.run` dentro de outros callbacks de DB.
- **Impact:** Quase impossível tratar erros corretamente; vazamentos de response.
- **Recommendation:** `async/await` + `util.promisify`. Ver playbook §6.

### `SECRET_LEAK_IN_LOGS`
- **MVC violation:** Camada de View/Controller logando credenciais.
- **Signals:** `console.log`/`print`/`logger.info` contendo `password`, `card`, `key`, `token`, `secret`, ou variáveis de config sensíveis.
- **Impact:** Credenciais aparecem em arquivos de log e ferramentas de observabilidade.
- **Recommendation:** Remover o log; nunca registrar dado sensível. Em logs estruturados, usar redaction.

### `SECRET_LEAK_IN_RESPONSE_HEALTH`
- **MVC violation:** Endpoint de diagnóstico vazando config.
- **Signals:** `/health`, `/status`, `/info` retornando `secret_key`, `db_url`, `api_key`.
- **Impact:** Endpoint público vaza segredos a qualquer scanner.
- **Recommendation:** Health = `{ status, version }`. Nada mais.

### `BROKEN_CASCADE_DELETE`
- **MVC violation:** Modelo sem integridade referencial.
- **Signals:** `DELETE FROM users WHERE id = ?` sem deletar dependências (pedidos, enrollments, payments) e sem `ON DELETE CASCADE` declarado no schema.
- **Impact:** Dados órfãos; estatísticas e relatórios ficam inconsistentes.
- **Recommendation:** Cascade explícito (FK com `ON DELETE CASCADE` ou exclusão programática em transação).

### `FAKE_AUTH_TOKEN`
- **MVC violation:** Controller emitindo token sem assinatura.
- **Signals:** `return 'token-' + str(user.id)`, `'fake-jwt-' + ...`, ou login devolvendo um token sem `jwt.sign`/`jwt.encode` com chave.
- **Impact:** Qualquer cliente forja tokens; auth efetivamente desligada.
- **Recommendation:** `pyjwt`/`jsonwebtoken` com chave de env, expiração e algoritmo HS256/RS256.

### `GLOBAL_MUTABLE_STATE`
- **MVC violation:** Persistência/cache fora da camada apropriada.
- **Signals:** Variável global `let cache = {}`, `globalCache`, `db_connection = None` no nível de módulo, mutada em vários pontos.
- **Impact:** Race conditions sob concorrência; testes acoplados; memory leaks.
- **Recommendation:** Conexão por request (DI), cache instanciado no composition root.

---

## MEDIUM

### `N_PLUS_ONE_QUERY`
- **MVC violation:** Model emitindo queries em loop.
- **Signals:**
  - Python: `for row in rows: cursor.execute(...)` com query usando `row["..."]`.
  - SQLAlchemy: `for x in items: User.query.get(x.user_id)`.
  - Node: `forEach(item => db.get(... item.id ...))` aninhado.
- **Impact:** N requisições no DB para uma operação que poderia ser 1 com JOIN; latência cresce linearmente.
- **Recommendation:** JOIN no SQL, ou eager loading do ORM (`relationship(..., lazy='joined')`). Ver playbook §9.

### `DUPLICATE_VALIDATION_LOGIC`
- **MVC violation:** Mesma regra repetida em múltiplos pontos da View/Controller.
- **Signals:** Bloco `if not data: ... if 'x' not in data: ... if x < 0: ...` quase idêntico em criar/atualizar.
- **Impact:** Drift entre validações; bugs assimétricos.
- **Recommendation:** Extrair para função/schema (marshmallow, pydantic, joi).

### `BARE_EXCEPT_OR_SWALLOWED_ERROR`
- **MVC violation:** View/Controller engolindo falhas.
- **Signals:**
  - Python: `except:` (sem classe) ou `except Exception:` retornando erro genérico sem log.
  - Node: `catch(err) {}` ou `catch(err) { return res.status(500).send("Erro DB") }`.
- **Impact:** Bugs silenciosos em produção; difícil diagnosticar incidentes.
- **Recommendation:** Capturar exceções específicas e logar com stack trace. Centralizar em middleware.

### `BLUEPRINT_OR_ROUTER_LEAK`
- **MVC violation:** Roteamento de um domínio dentro do arquivo de outro.
- **Signals:** Blueprint `report_bp` registrando rotas `/categories` em vez de criar `category_bp`.
- **Impact:** Acoplamento implícito; quebra de princípio de coesão.
- **Recommendation:** 1 blueprint/router por domínio.

### `UNVALIDATED_INPUT_TYPE`
- **MVC violation:** View aceitando tipos arbitrários.
- **Signals:** `req.body.x` usado direto sem `typeof`/coerção; `request.get_json().get('x')` usado em comparação numérica sem `int(...)`.
- **Impact:** Crashes ou comportamento bizarro com payload malformado.
- **Recommendation:** Schema validation no edge (pydantic/marshmallow/joi/zod).

### `MISSING_CASCADE_OR_TRANSACTION`
- **MVC violation:** Operações multi-step sem atomicidade.
- **Signals:** Sequência de INSERTs em diferentes tabelas (ex: pedido + itens_pedido + estoque) sem `BEGIN`/`COMMIT` ou `with db.session.begin()`.
- **Impact:** Estado parcial em caso de falha — pedido criado mas itens não.
- **Recommendation:** Envolver em transação.

---

## LOW

### `MAGIC_NUMBER`
- **Signals:** Literais numéricos não-óbvios em validação ou regra (`if len(x) > 200`, `if total > 10000`).
- **Recommendation:** Constantes nomeadas em `config/` ou módulo de constants.

### `DEAD_CODE_OR_UNUSED_IMPORT`
- **Signals:**
  - Python: imports não-usados (`import sqlite3` sem referência).
  - Node: variável exportada nunca atribuída/lida (ex: `totalRevenue` em `utils.js`).
- **Recommendation:** Remover.

### `PRINT_OR_CONSOLE_LOG`
- **Signals:** `print(...)`/`console.log(...)` em código não-CLI.
- **Recommendation:** Trocar por `logging`/`winston`/`pino` configurado no `config/`.

### `LOOSE_TYPE_CHECK`
- **Signals:** Python `type(x) == list`; JS `typeof x == 'object'` para checar arrays.
- **Recommendation:** `isinstance(x, list)` / `Array.isArray(x)`.

### `INADEQUATE_HTTP_STATUS`
- **Signals:** `400` para "pagamento recusado" (deveria ser `402`); `500` quando deveria ser `404`.
- **Recommendation:** Mapear corretamente conforme RFC 7231.

---

## DEPRECATED_API (severidade contextual)

**Esta categoria é obrigatória no desafio.** Reporte sempre que detectar uso de API obsoleta, com a severidade do impacto (geralmente `MEDIUM`, `HIGH` se a API foi removida na versão atual da dependência).

### Python
| API antiga | API moderna | Notas |
|---|---|---|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` | Deprecated em Python 3.12; `utcnow` retorna naive datetime sem tz, fonte de bugs. |
| `flask.Markup` | `from markupsafe import Markup` | Removido em Flask 2.3+. |
| `flask.escape` | `from markupsafe import escape` | idem. |
| `werkzeug.urls.url_quote` | `urllib.parse.quote` | Removido em Werkzeug 3.0. |
| `sqlalchemy.ext.declarative.declarative_base()` | `sqlalchemy.orm.declarative_base()` | SQLAlchemy 2.0+. |
| `Model.query.get(id)` (Flask-SQLAlchemy) | `db.session.get(Model, id)` | Legacy Query API descontinuada em SQLAlchemy 2.x. |

### Node.js
| API antiga | API moderna | Notas |
|---|---|---|
| `new Buffer(x)` | `Buffer.from(x)` ou `Buffer.alloc(n)` | Construtor `Buffer` deprecated desde Node 10. |
| `crypto.createCipher` | `crypto.createCipheriv` | Sem IV é inseguro. |
| `body-parser` (separado) | `express.json()` / `express.urlencoded()` | Built-in desde Express 4.16. |
| `request` (npm) | `node-fetch`/`axios`/`undici` | `request` arquivado. |
| `fs.exists` | `fs.access` ou `fs.stat` | Deprecated. |
| `url.parse` | `new URL(...)` (WHATWG) | Legacy URL API. |
| `process.binding(...)` | APIs públicas equivalentes | Deprecated para uso fora do core. |

**Procedimento:** `Grep` pelos padrões antigos. Se acertar, abrir um finding `DEPRECATED_API` com severidade conforme: HIGH se a API foi removida na versão da dependência declarada no manifesto; MEDIUM se ainda existe mas com warning.

---

## Como contar findings

- 1 anti-pattern em N arquivos = N findings (cada arquivo é um finding separado).
- 1 anti-pattern repetido na **mesma função** com sinais idênticos pode ser agrupado como 1 finding com range de linhas.
- Sempre gerar **mínimo 5 findings** se o projeto tem code smells visíveis. Se você acha < 5, releia o catálogo — provavelmente ignorou DEPRECATED_API ou MAGIC_NUMBER.
