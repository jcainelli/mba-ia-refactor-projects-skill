# Guidelines do MVC Alvo — Fase 3

A skill refatora **sempre** para o mesmo layout, independente da stack. As pastas têm os mesmos nomes em Python e Node — só as extensões mudam.

---

## Layout-alvo

```
src/
├── config/
│   ├── settings.{py,js}       # lê env vars via os.environ / process.env
│   └── database.{py,js}       # construção/factory da conexão
├── models/
│   ├── <entidade>_model.{py,js}
│   └── ...                     # 1 arquivo por entidade do domínio
├── views/
│   ├── <entidade>_routes.{py,js}
│   └── ...                     # blueprints/routers — só roteamento + (de)serialização
├── controllers/
│   ├── <entidade>_controller.{py,js}
│   └── ...                     # orquestração do fluxo, chama models/services
├── services/
│   ├── <serviço>_service.{py,js}
│   └── ...                     # regras cross-entity, integrações externas (email, payment)
├── middlewares/
│   ├── error_handler.{py,js}   # captura exceções globalmente
│   └── auth.{py,js}            # se houver autenticação
└── app.{py,js}                 # composition root: cria app, registra rotas, sobe servidor

.env                            # gitignored — segredos e configs por ambiente
.env.example                    # commitado — template documentando as vars
```

Na raiz do projeto (fora de `src/`), preserve `requirements.txt`/`package.json`, `README.md`, `seed.{py,js}` se existirem.

---

## Responsabilidades de cada camada

### `config/`
- Carrega `.env` (use `python-dotenv` em Python, `dotenv` em Node).
- Expõe um objeto/módulo `settings` com atributos tipados (`SECRET_KEY`, `DATABASE_URL`, `DEBUG`, etc.).
- Constrói/exporta a conexão do banco (mas não a instancia globalmente — usa factory).
- **Nunca** contém literais de credenciais. Se uma var é obrigatória, o módulo deve falhar no boot caso esteja ausente.

### `models/`
- Apenas estrutura de dados + persistência + validações de **domínio** (ex: "preço não pode ser negativo").
- Sem `print`/`console.log`. Sem chamadas a serviços externos. Sem orquestração de fluxo.
- 1 arquivo por entidade. `Produto` em `produto_model.py`, `Usuario` em `usuario_model.py`.
- Em ORM (SQLAlchemy/Sequelize): a classe model + métodos de acesso simples (CRUD).
- Em SQL puro: funções `get_x_by_id`, `create_x`, etc., com queries **parametrizadas**.

### `views/` (a.k.a. routes/blueprints/routers)
- Recebe HTTP, valida shape do payload (schema), chama o controller, devolve resposta serializada.
- **Sem regras de negócio.** Se você está escrevendo um `if x in [...]` que decide comportamento de domínio, isso pertence ao controller.
- Em Flask: `Blueprint`. Em Express: `Router`. 1 blueprint/router por entidade.
- Pode usar serializers (marshmallow/pydantic/joi/zod) para validar entrada.

### `controllers/`
- Orquestra o fluxo de uma operação: valida regras de negócio, chama 1+ models/services, monta a resposta.
- Recebe dados já validados pela view.
- Não toca em `request`/`response` diretamente — devolve dicts/objetos puros que a view serializa.
- 1 arquivo por entidade ou agrupamento lógico (ex: `pedido_controller.py` cuida de criar pedido + abate estoque + dispara notificação).

### `services/`
- Regras cross-entity (ex: "criar pedido envolve produto, usuário, estoque, notificação").
- Integrações com APIs externas (gateway de pagamento, SMTP, push).
- Sem dependência de HTTP. Pode ser instanciado em testes unitários sem Flask/Express rodando.

### `middlewares/`
- `error_handler`: captura exceções não-tratadas e devolve JSON consistente. Em Flask: `@app.errorhandler(Exception)`. Em Express: `app.use((err, req, res, next) => ...)`.
- `auth`: valida token/sessão antes de roteador. Em Flask: decorator. Em Express: `app.use('/api', authMiddleware, router)`.
- Logging estruturado.

### `app.{py,js}` (composition root)
- Importa config, models, views, middlewares e os **fia** (registra blueprints, monta a app, sobe o servidor).
- Único arquivo onde imports cruzam camadas livremente.
- Não contém regras de negócio. Não tem `if`s de domínio.

---

## Regras invariantes

1. **Zero queries em controller.** Controller chama o model, que executa a query.
2. **Zero lógica em view.** View só roteia. Toda condicional de domínio vai para controller/service.
3. **Zero literais de config no código.** Tudo via `config/settings`. Inclusive ports, default messages, domínios CORS.
4. **Zero acesso direto ao request/response fora de views/middlewares.** Controllers operam sobre objetos planos.
5. **Imports respeitam a hierarquia:** view → controller → service → model → config. Nunca o contrário (controller não importa view, model não importa controller).
6. **Senhas nunca em logs nem em respostas.** Modelo de usuário deve ter `to_safe_dict()`/`to_public_dict()` que omite o hash.

---

## Convenções por linguagem

### Python/Flask
- `Blueprint` por entidade em `views/`.
- `db = SQLAlchemy()` em `config/database.py`, `db.init_app(app)` em `app.py`.
- Error handler via `@app.errorhandler` em `middlewares/error_handler.py` registrado no `app.py`.
- Dotenv: `from dotenv import load_dotenv; load_dotenv()` no topo de `config/settings.py`.

### Node/Express
- `Router` por entidade em `views/`.
- DB exportada de `config/database.js` (factory que retorna a conexão pronta).
- Error handler em `middlewares/errorHandler.js`, registrado **por último** no `app.js`.
- Dotenv: `require('dotenv').config()` na primeira linha de `config/settings.js`.
- Async/await **obrigatório** — sem callback hell.

---

## Composition root — exemplo Python/Flask

```python
# src/app.py
from flask import Flask
from flask_cors import CORS
from config.settings import settings
from config.database import db
from views.produto_routes import produto_bp
from views.usuario_routes import usuario_bp
from views.pedido_routes import pedido_bp
from middlewares.error_handler import register_error_handlers

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL
    CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    register_error_handlers(app)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
```

## Composition root — exemplo Node/Express

```javascript
// src/app.js
require('dotenv').config();
const express = require('express');
const { settings } = require('./config/settings');
const { initDb } = require('./config/database');
const userRouter = require('./views/userRoutes');
const courseRouter = require('./views/courseRoutes');
const checkoutRouter = require('./views/checkoutRoutes');
const errorHandler = require('./middlewares/errorHandler');

async function bootstrap() {
    const app = express();
    app.use(express.json());

    await initDb();

    app.use('/api/users', userRouter);
    app.use('/api/courses', courseRouter);
    app.use('/api/checkout', checkoutRouter);

    app.use(errorHandler); // sempre por último

    app.listen(settings.port, () => console.log(`Server on ${settings.port}`));
}

bootstrap();
```

---

## Adaptação por categoria de arquitetura inicial

(Casa com `analysis-heuristics.md` §5.)

### `monolithic-flat`
- Criar `src/` do zero.
- Mover `app.py`/`app.js` para `src/app.py`/`src/app.js`.
- Atualizar entrypoint nas docs/scripts (`python src/app.py` ou `node src/app.js`).

### `partially-layered`
- **Promover** `models/` e `routes/` existentes para `src/models/` e `src/views/`.
- Criar pastas faltantes (`controllers/`, `config/`, `middlewares/`, `services/`).
- Extrair lógica das `routes/` para `controllers/`.
- Mover `services/` existentes para `src/services/`.
- Mover `database.py` (config raiz) para `src/config/database.py`.
- **Preservar nomes de blueprints/routes** para não quebrar contratos.

### `layered`
- Reorganizar apenas se camadas estão fora do padrão (ex: `controllers/` na raiz).
- Senão, focar em correções pontuais (segurança, deprecated, N+1).
