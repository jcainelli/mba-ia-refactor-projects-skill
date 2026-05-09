# Playbook de Refatoração — Fase 3

Este playbook tem **transformações concretas** para cada categoria do `antipatterns-catalog.md`. Cada padrão tem: quando aplicar, código antes (ruim), código depois (bom), notas de migração.

Use a numeração (`§N`) para referenciar a partir do relatório da Fase 2.

---

## §1. Extract config from hardcoded values

**Quando aplicar:** anti-pattern `HARDCODED_SECRET`, port literal em `app.run`/`app.listen`, URLs do CORS literais, credenciais de SMTP/gateway.

### Antes (Python/Flask)

```python
# app.py
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)
```

### Depois (Python/Flask)

```python
# src/config/settings.py
import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    SECRET_KEY = os.environ["SECRET_KEY"]  # KeyError se faltar — falha no boot
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///loja.db")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", "5000"))
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

settings = Settings()
```

```bash
# .env (gitignored)
SECRET_KEY=<gerar com python -c "import secrets; print(secrets.token_hex(32))">
DATABASE_URL=sqlite:///loja.db
DEBUG=false
```

```bash
# .env.example (commitado, sem valores)
SECRET_KEY=
DATABASE_URL=
DEBUG=
HOST=
PORT=
CORS_ORIGINS=
```

### Antes (Node/Express)

```javascript
// utils.js
const config = {
    dbPass: "senha_super_secreta_prod_123",
    paymentGatewayKey: "pk_live_1234567890abcdef",
    port: 3000
};
```

### Depois (Node/Express)

```javascript
// src/config/settings.js
require('dotenv').config();

function required(name) {
    const v = process.env[name];
    if (!v) throw new Error(`Missing env var: ${name}`);
    return v;
}

const settings = {
    paymentGatewayKey: required('PAYMENT_GATEWAY_KEY'),
    smtpUser: process.env.SMTP_USER || 'no-reply@example.com',
    port: parseInt(process.env.PORT || '3000', 10),
    nodeEnv: process.env.NODE_ENV || 'development',
};

module.exports = { settings };
```

**Notas:**
- Sempre commit `.env.example` documentando as vars.
- Adicione `.env` ao `.gitignore` se ainda não está.
- Para SECRET_KEY, gere uma nova — a antiga foi comprometida ao estar no Git.

---

## §2. Split god file by domain

**Quando aplicar:** `GOD_FILE_OR_CLASS`. Arquivo > 300 LOC misturando entidades.

### Antes (Python)

```python
# models.py (350 linhas, 4 entidades misturadas)
def get_todos_produtos(): ...
def criar_produto(...): ...
def get_todos_usuarios(): ...
def login_usuario(...): ...
def criar_pedido(...): ...
def relatorio_vendas(): ...
```

### Depois (Python)

```
src/models/
├── produto_model.py      # get_todos_produtos, get_produto_por_id, criar_produto, ...
├── usuario_model.py      # get_todos_usuarios, criar_usuario, autenticar_usuario
└── pedido_model.py       # criar_pedido, get_pedidos_usuario, atualizar_status
```

```python
# src/models/produto_model.py
from config.database import get_connection

def get_todos_produtos():
    db = get_connection()
    rows = db.execute("SELECT * FROM produtos").fetchall()
    return [dict(r) for r in rows]

def get_produto_por_id(produto_id):
    db = get_connection()
    row = db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return dict(row) if row else None
```

### Antes (Node — God class)

```javascript
class AppManager {
    initDb() { /* schema */ }
    setupRoutes(app) {
        app.post('/api/checkout', /* 60 linhas */);
        app.get('/api/admin/financial-report', /* 50 linhas */);
        app.delete('/api/users/:id', /* 7 linhas */);
    }
}
```

### Depois (Node)

```
src/
├── config/database.js
├── models/{userModel,courseModel,enrollmentModel,paymentModel}.js
├── controllers/{checkoutController,reportController,userController}.js
└── views/{checkoutRoutes,reportRoutes,userRoutes}.js
```

**Notas:**
- Mantenha o nome das funções públicas para evitar churn em testes existentes.
- Atualize todos os `import`/`require` quebrados em uma única passagem.

---

## §3. Move business logic from view to controller

**Quando aplicar:** `BUSINESS_LOGIC_IN_VIEW`. Validação ou regra dentro de handler de rota.

### Antes (Flask blueprint)

```python
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    title = data.get('title')
    if not title or len(title) < 3 or len(title) > 200:
        return jsonify({'error': 'Título inválido'}), 400
    if data.get('priority', 3) < 1 or data.get('priority', 3) > 5:
        return jsonify({'error': 'Prioridade inválida'}), 400
    # ... mais 30 linhas de regras + persistência ...
    task = Task(...)
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201
```

### Depois

```python
# src/views/task_routes.py
from controllers.task_controller import create_task as ctrl_create_task

@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json() or {}
    task, error = ctrl_create_task(data)
    if error:
        return jsonify({'error': error}), 400
    return jsonify(task), 201
```

```python
# src/controllers/task_controller.py
from models.task_model import insert_task
from utils.constants import VALID_STATUSES, MIN_TITLE_LEN, MAX_TITLE_LEN

def create_task(data):
    title = (data.get('title') or '').strip()
    if not (MIN_TITLE_LEN <= len(title) <= MAX_TITLE_LEN):
        return None, f'Título deve ter entre {MIN_TITLE_LEN} e {MAX_TITLE_LEN} caracteres'
    priority = data.get('priority', 3)
    if not (1 <= priority <= 5):
        return None, 'Prioridade deve ser entre 1 e 5'
    status = data.get('status', 'pending')
    if status not in VALID_STATUSES:
        return None, 'Status inválido'
    task = insert_task(title=title, priority=priority, status=status, ...)
    return task, None
```

**Notas:**
- View vira "fina" — apenas (a) parsing, (b) chamada ao controller, (c) serialização.
- Controller retorna `(resultado, erro)` ou levanta exceção custom (capturada pelo middleware §7).

---

## §4. Parameterize SQL queries

**Quando aplicar:** `SQL_INJECTION_STRING_CONCAT`.

### Antes

```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute(
    "INSERT INTO produtos (nome, preco) VALUES ('" + nome + "', " + str(preco) + ")"
)
query = "SELECT * FROM produtos WHERE 1=1"
if termo:
    query += " AND nome LIKE '%" + termo + "%'"
cursor.execute(query)
```

### Depois

```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute(
    "INSERT INTO produtos (nome, preco) VALUES (?, ?)",
    (nome, preco)
)
filters = ["1=1"]
params = []
if termo:
    filters.append("(nome LIKE ? OR descricao LIKE ?)")
    params += [f"%{termo}%", f"%{termo}%"]
cursor.execute("SELECT * FROM produtos WHERE " + " AND ".join(filters), params)
```

### Antes (Node)

```javascript
db.run(`INSERT INTO users (name, email, pass) VALUES ('${u}', '${e}', '${hash}')`);
```

### Depois (Node)

```javascript
db.run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [u, e, hash]);
```

**Notas:**
- O `LIKE %termo%` ainda é parametrizável — só passe o valor com os `%` já incluídos.
- Para queries dinâmicas (filtros opcionais), construa **placeholders**, não strings.
- `executemany` em Python vs `db.run` em loop — preserve a semântica.

---

## §5. Replace plaintext/MD5 with bcrypt/argon2

**Quando aplicar:** `PLAINTEXT_PASSWORD`, `WEAK_HASH_FOR_AUTH`.

### Antes (Python — plaintext)

```python
# database.py
cursor.executemany(
    "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
    [("Admin", "admin@loja.com", "admin123")]
)

# login
cursor.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
```

### Antes (Python — MD5)

```python
import hashlib
class User(db.Model):
    def set_password(self, pwd):
        self.password = hashlib.md5(pwd.encode()).hexdigest()
    def check_password(self, pwd):
        return self.password == hashlib.md5(pwd.encode()).hexdigest()
```

### Depois (Python)

```python
# requirements.txt: + bcrypt==4.*

import bcrypt

class User(db.Model):
    password_hash = db.Column(db.String(60), nullable=False)  # bcrypt = 60 chars

    def set_password(self, pwd: str) -> None:
        self.password_hash = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

    def check_password(self, pwd: str) -> bool:
        if not self.password_hash:
            return False
        return bcrypt.checkpw(pwd.encode(), self.password_hash.encode())
```

```python
# fluxo de login (controller)
user = get_usuario_por_email(email)
if user and user.check_password(senha):
    return user
```

### Antes (Node — função inventada)

```javascript
function badCrypto(pwd) {
    let hash = "";
    for(let i = 0; i < 10000; i++) hash += Buffer.from(pwd).toString('base64').substring(0, 2);
    return hash.substring(0, 10);
}
```

### Depois (Node)

```javascript
// package.json: + "bcrypt": "^5.1.0"
const bcrypt = require('bcrypt');

async function hashPassword(plain) {
    return bcrypt.hash(plain, 12);
}

async function verifyPassword(plain, hashed) {
    return bcrypt.compare(plain, hashed);
}
```

**Notas:**
- Migração: usuários existentes precisam re-hash. No projeto sample (DB em memória / SQLite efêmero), basta atualizar o seed.
- Coluna `senha`/`password` deve ser **renomeada** para `password_hash` para deixar o tipo de dado claro.
- Cost factor = 12 por padrão (bcrypt) — não menor.

---

## §6. Flatten callback hell

**Quando aplicar:** `CALLBACK_HELL`.

### Antes

```javascript
this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    if (err || !course) return res.status(404).send("...");
    this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
        if (err) return res.status(500).send("...");
        let processPaymentAndEnroll = (userId) => {
            this.db.run("INSERT INTO enrollments ...", [userId, cid], function(err) {
                if (err) return res.status(500).send("...");
                self.db.run("INSERT INTO payments ...", [...], function(err) {
                    if (err) return res.status(500).send("...");
                    self.db.run("INSERT INTO audit_logs ...", [...], (err) => {
                        res.status(200).json({ ... });
                    });
                });
            });
        };
        if (!user) {
            this.db.run("INSERT INTO users ...", [...], function(err) {
                processPaymentAndEnroll(this.lastID);
            });
        } else {
            processPaymentAndEnroll(user.id);
        }
    });
});
```

### Depois

```javascript
// src/config/database.js — wrap sqlite3 com util.promisify
const { promisify } = require('util');
function promisifyDb(db) {
    return {
        get: promisify(db.get.bind(db)),
        all: promisify(db.all.bind(db)),
        run: (...args) => new Promise((resolve, reject) =>
            db.run(...args, function (err) { err ? reject(err) : resolve(this); })
        ),
    };
}

// src/controllers/checkoutController.js
async function checkout({ name, email, password, courseId, card }) {
    const course = await db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [courseId]);
    if (!course) throw new NotFoundError('Curso não encontrado');

    let user = await db.get("SELECT id FROM users WHERE email = ?", [email]);
    if (!user) {
        const hash = await hashPassword(password || '');
        const inserted = await db.run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [name, email, hash]);
        user = { id: inserted.lastID };
    }

    const status = await processPayment(card, course.price);
    if (status === 'DENIED') throw new PaymentDeniedError('Pagamento recusado');

    const enrollment = await db.run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [user.id, courseId]);
    await db.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enrollment.lastID, course.price, status]);
    await db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [`Checkout curso ${courseId} por ${user.id}`]);

    return { enrollmentId: enrollment.lastID, course: course.title };
}
```

**Notas:**
- Use `try/catch` no controller, ou deixe a exception subir para o middleware de erro (§7).
- Erros customizados (`NotFoundError`, `PaymentDeniedError`) viram `404`/`402` no middleware.

---

## §7. Centralize error handling

**Quando aplicar:** `BARE_EXCEPT_OR_SWALLOWED_ERROR`, ou repetição massiva de `try/except` retornando `500` em todo controller.

### Antes (Python — repetido em N endpoints)

```python
@app.route('/produtos', methods=['GET'])
def listar_produtos():
    try:
        produtos = models.get_todos_produtos()
        return jsonify({"dados": produtos, "sucesso": True}), 200
    except Exception as e:
        print("ERRO: " + str(e))
        return jsonify({"erro": str(e)}), 500
```

### Depois

```python
# src/middlewares/error_handler.py
import logging
from flask import jsonify

class AppError(Exception):
    status_code = 500
    def __init__(self, message, status_code=None):
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code

class NotFoundError(AppError):
    status_code = 404

class ValidationError(AppError):
    status_code = 400

def register_error_handlers(app):
    log = logging.getLogger(__name__)

    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': str(err)}), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        log.exception("Unexpected error")
        return jsonify({'error': 'Internal server error'}), 500
```

```python
# views/produto_routes.py — view enxuta
@produto_bp.route('/produtos', methods=['GET'])
def listar_produtos():
    return jsonify({'dados': controller.list_produtos()}), 200
```

### Node

```javascript
// src/middlewares/errorHandler.js
class AppError extends Error {
    constructor(message, statusCode = 500) {
        super(message);
        this.statusCode = statusCode;
    }
}

function errorHandler(err, req, res, next) {
    const status = err.statusCode || 500;
    if (status >= 500) console.error(err);
    res.status(status).json({ error: err.message || 'Internal server error' });
}

module.exports = { AppError, errorHandler };
```

```javascript
// app.js — registra por último
app.use(errorHandler);
```

**Notas:**
- Controllers passam a **levantar** exceções em vez de retornar `(result, error)`. Mais idiomático.
- Logging deve ser **estruturado**, não `print`/`console.log`.

---

## §8. Replace deprecated APIs

**Quando aplicar:** `DEPRECATED_API`. Use a tabela do `antipatterns-catalog.md` como referência.

### Python

```python
# antes
from datetime import datetime
created_at = datetime.utcnow()  # deprecated em 3.12

# depois
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)
```

```python
# antes (Flask-SQLAlchemy)
user = User.query.get(user_id)

# depois (SQLAlchemy 2.x)
user = db.session.get(User, user_id)
```

### Node

```javascript
// antes
const buf = new Buffer(input);

// depois
const buf = Buffer.from(input);
```

```javascript
// antes (Express < 4.16)
const bodyParser = require('body-parser');
app.use(bodyParser.json());

// depois
app.use(express.json());
```

**Notas:**
- Atualize tipos: `datetime.now(timezone.utc)` retorna aware datetime — modelos com `default=datetime.utcnow` passam a precisar de timezone-aware columns.
- Para SQLAlchemy 2.x: prefira `db.session.execute(select(...))` em queries complexas.

---

## §9. Eliminate N+1 queries

**Quando aplicar:** `N_PLUS_ONE_QUERY`.

### Antes (SQL puro)

```python
def get_pedidos_usuario(usuario_id):
    pedidos = db.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,)).fetchall()
    result = []
    for pedido in pedidos:
        itens = db.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (pedido["id"],)).fetchall()
        for item in itens:
            prod = db.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],)).fetchone()
            ...
```

### Depois

```python
def get_pedidos_usuario(usuario_id):
    rows = db.execute("""
        SELECT
            p.id AS pedido_id, p.status, p.total, p.criado_em,
            i.produto_id, i.quantidade, i.preco_unitario,
            pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = i.produto_id
        WHERE p.usuario_id = ?
        ORDER BY p.criado_em DESC, p.id
    """, (usuario_id,)).fetchall()
    # Agrupa em memória — 1 query, não 1 + N + N*M
    return _group_pedidos(rows)
```

### Antes (SQLAlchemy)

```python
tasks = Task.query.all()
for t in tasks:
    user = User.query.get(t.user_id)  # +1 query por task
```

### Depois (SQLAlchemy)

```python
from sqlalchemy.orm import joinedload
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
for t in tasks:
    user = t.user  # já carregado
```

**Notas:**
- JOIN é a opção universal (SQL puro / qualquer ORM).
- Eager loading do ORM é mais limpo quando há relationship declarado.

---

## §10. Sanitize response payloads

**Quando aplicar:** `PII_LEAK_IN_RESPONSE`. Senhas/tokens/segredos no JSON.

### Antes

```python
class User(db.Model):
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': self.password,  # vaza o hash
            'role': self.role,
        }
```

### Depois

```python
class User(db.Model):
    PUBLIC_FIELDS = ('id', 'name', 'email', 'role', 'active', 'created_at')

    def to_public_dict(self):
        return {f: getattr(self, f) for f in self.PUBLIC_FIELDS}

    # to_dict() removido — sempre passar pelo to_public_dict
```

### Antes (Flask /health)

```python
return jsonify({
    "status": "ok",
    "secret_key": "minha-chave-super-secreta-123"
})
```

### Depois

```python
return jsonify({
    "status": "ok",
    "version": settings.VERSION,
    "uptime": _uptime_seconds()
})
```

**Notas:**
- Allow-list é sempre mais seguro do que blacklist.
- `/health` não deve revelar nada além de status e versão.

---

## §11. Eliminate global mutable state (bonus)

**Quando aplicar:** `GLOBAL_MUTABLE_STATE`.

### Antes

```python
# database.py
db_connection = None
def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("loja.db", check_same_thread=False)
    return db_connection
```

### Depois

```python
# src/config/database.py — Flask: usa g + close em teardown
import sqlite3
from flask import g, current_app

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DB_PATH'])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(_=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
```

**Notas:**
- Em Flask, `g` é por-request — sem race conditions.
- Em Node, encapsule a conexão em um módulo factory + reuse via DI no controller.

---

## §12. Wrap multi-step operations in transactions (bonus)

**Quando aplicar:** `MISSING_CASCADE_OR_TRANSACTION`. Ex: criação de pedido com items + abate de estoque.

### Antes

```python
cursor.execute("INSERT INTO pedidos ...")
pedido_id = cursor.lastrowid
for item in itens:
    cursor.execute("INSERT INTO itens_pedido ...")
    cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", ...)
db.commit()  # se algo entre os INSERTs falhar, estado parcial
```

### Depois

```python
db = get_db()
try:
    db.execute("BEGIN")
    cursor = db.cursor()
    cursor.execute("INSERT INTO pedidos ...")
    pedido_id = cursor.lastrowid
    for item in itens:
        cursor.execute("INSERT INTO itens_pedido ...")
        result = cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?", (qtd, prod_id, qtd))
        if result.rowcount == 0:
            raise ValidationError(f"Estoque insuficiente para produto {prod_id}")
    db.commit()
except Exception:
    db.rollback()
    raise
```

**Notas:**
- `UPDATE ... AND estoque >= ?` evita race condition (check + update atômico).
- Em SQLAlchemy: `with db.session.begin(): ...`.

---

## Ordem de aplicação recomendada (Fase 3)

1. **§1 — Extract config** (necessário antes de tudo, senão você não consegue rodar com env diferente).
2. **§2 — Split god file** (cria a estrutura de pastas alvo).
3. **§4 — Parameterize SQL** (segurança CRITICAL — não deixe pra depois).
4. **§5 — Replace weak hash** (segurança CRITICAL).
5. **§3 — Move logic to controller** (estrutura).
6. **§6 — Flatten callbacks** (Node — clareza).
7. **§7 — Centralize errors** (middleware — depende da estrutura existir).
8. **§8 — Replace deprecated APIs** (cleanup — pode rodar a qualquer hora).
9. **§9 — Eliminate N+1** (performance).
10. **§10 — Sanitize payloads** (segurança visível).
11. **§11/§12 — Bonus** (state, transações).

Após cada bloco, rode o teste de boot + curl. Não acumule mudanças sem validar.
