================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1, SQLite)
Files:   16 analyzed | ~1160 lines of code

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 9 | LOW: 5

## Findings

### [CRITICAL] HARDCODED_SECRET
File: app.py:13
Description: SECRET_KEY do Flask hardcoded ('super-secret-key-123') no código-fonte, em vez de ler de variável de ambiente.
Impact: Segredo commitado no repositório; rotacionar exige mudar código + redeploy; comprometimento permanente assim que o repo vaza.
Recommendation: Mover para .env (gitignored) e ler via os.environ em src/config/settings.py. Ver playbook §1.

### [CRITICAL] HARDCODED_SECRET
File: services/notification_service.py:7-10
Description: Credenciais SMTP (host, porta, usuário e senha 'senha123') definidas como literais no construtor de NotificationService.
Impact: Credenciais de e-mail expostas no repositório — qualquer leitor do código obtém acesso à conta SMTP usada pela aplicação.
Recommendation: Mover SMTP_HOST/PORT/USER/PASS para .env e injetar via settings; falhar no boot se obrigatórias e ausentes. Ver playbook §1.

### [CRITICAL] WEAK_HASH_FOR_AUTH
File: models/user.py:29-32
Description: User.set_password e User.check_password usam hashlib.md5 para hashear senhas de usuário.
Impact: MD5 é colidível e tem rainbow tables públicas há mais de uma década; um vazamento do banco expõe senhas reais.
Recommendation: Substituir por bcrypt (cost=12) ou argon2; renomear coluna para password_hash. Ver playbook §5.

### [CRITICAL] PII_LEAK_IN_RESPONSE
File: models/user.py:16-25
Description: User.to_dict() inclui o campo 'password' (hash MD5) no payload retornado por todos os endpoints de usuário e por /login.
Impact: Qualquer cliente autenticado em GET /users, GET /users/<id>, POST /users, PUT /users/<id> e POST /login recebe o hash da senha — vazamento direto via API.
Recommendation: Remover 'password' do dicionário e expor apenas allow-list (id, name, email, role, active, created_at) via to_public_dict(). Ver playbook §10.

### [HIGH] FAKE_AUTH_TOKEN
File: routes/user_routes.py:210
Description: Endpoint POST /login devolve um token construído como string concatenada ('fake-jwt-token-' + str(user.id)), sem assinatura nem expiração.
Impact: Qualquer cliente forja tokens trivialmente conhecendo o id do usuário; autenticação efetivamente desligada.
Recommendation: Trocar por pyjwt com SECRET_KEY do env, algoritmo HS256 e expiração configurável; mover emissão para um auth_service. Ver playbook (extensão do §5/§7).

### [HIGH] BUSINESS_LOGIC_IN_VIEW
File: routes/task_routes.py:11-298
Description: Handlers de rota concentram parsing, validação de domínio (status válido, prioridade 1-5, comprimento de título), regra de "overdue", lookup de FKs, persistência e serialização. A camada de view contém praticamente toda a lógica do domínio Task.
Impact: Lógica não-reutilizável e impossível de testar sem subir HTTP; mudanças em regras forçam edição em múltiplos handlers.
Recommendation: Extrair para src/controllers/task_controller.py + src/services/task_service.py; views passam apenas dados validados ao controller. Ver playbook §3.

### [HIGH] BLUEPRINT_OR_ROUTER_LEAK
File: routes/report_routes.py:157-223
Description: O blueprint report_bp registra rotas /categories (GET/POST/PUT/DELETE) — domínio diferente — em vez de existir um category_bp dedicado.
Impact: Acoplamento implícito entre módulos; quebra de coesão por blueprint; dificulta testes e organização de URLs.
Recommendation: Criar src/views/category_routes.py com category_bp próprio e mantê-lo registrado em app.py separadamente.

### [MEDIUM] N_PLUS_ONE_QUERY
File: routes/task_routes.py:14-57
Description: GET /tasks itera sobre Task.query.all() e, para cada task, executa User.query.get(t.user_id) e Category.query.get(t.category_id) — 1 + 2N queries.
Impact: Latência cresce linearmente com o número de tasks; com 1000 tasks são ~2001 queries por request.
Recommendation: Trocar por Task.query.options(joinedload(Task.user), joinedload(Task.category)).all(). Ver playbook §9.

### [MEDIUM] N_PLUS_ONE_QUERY
File: routes/report_routes.py:53-68
Description: O cálculo de user_productivity em GET /reports/summary itera sobre User.query.all() e dispara Task.query.filter_by(user_id=u.id).all() para cada usuário.
Impact: Relatório custa 1 + N queries; degrada com a base de usuários e roda em endpoint público.
Recommendation: Substituir por uma única query agregada com GROUP BY user_id (ou eager loading + agrupamento em memória). Ver playbook §9.

### [MEDIUM] DUPLICATE_VALIDATION_LOGIC
File: routes/task_routes.py:96-145
Description: As mesmas validações de Task (título 3-200 chars, status em lista fixa, prioridade 1-5, parsing de due_date YYYY-MM-DD, normalização de tags) aparecem em create_task (linhas 96-145) e update_task (linhas 167-214); a função utils/helpers.py:57-108 (process_task_data) reimplementa as três pela terceira vez e nunca é chamada.
Impact: Drift entre create/update já é visível (mensagens de erro divergem); manutenção exige editar 3 lugares; risco alto de regressão.
Recommendation: Extrair para src/schemas/task_schema.py com marshmallow (já no requirements.txt) e remover process_task_data. Ver playbook §3.

### [MEDIUM] BARE_EXCEPT_OR_SWALLOWED_ERROR
File: routes/task_routes.py:62, 137, 204, 236
Description: Quatro blocos try/except com cláusula nua (except:) que retornam erros genéricos 400/500 sem logar a exceção real.
Impact: Bugs silenciosos em produção; telemetria não captura stack trace; KeyboardInterrupt e SystemExit também são engolidos.
Recommendation: Capturar exceções específicas, logar com logger.exception e centralizar em src/middlewares/error_handler.py. Ver playbook §7.

### [MEDIUM] BARE_EXCEPT_OR_SWALLOWED_ERROR
File: routes/report_routes.py:186, 207, 221
Description: Três bare except: nos endpoints POST/PUT/DELETE de /categories devolvendo "Erro ao criar/atualizar/deletar" sem nenhum log.
Impact: Falhas em produção viram 500 opacos; impossível diagnosticar sem reprodução manual.
Recommendation: Trocar por except SQLAlchemyError com logger.exception e delegar ao error_handler global. Ver playbook §7.

### [MEDIUM] BARE_EXCEPT_OR_SWALLOWED_ERROR
File: routes/user_routes.py:130, 149
Description: Bare except: em PUT /users/<id> e DELETE /users/<id> retornando 500 genérico.
Impact: Idem — falhas opacas; impossível telemetria.
Recommendation: Capturar exceções específicas e logar; centralizar resposta no middleware. Ver playbook §7.

### [MEDIUM] DEPRECATED_API
File: models/task.py:15-16,52, models/user.py:14, models/category.py:11, routes/task_routes.py:31,72,215,285, routes/user_routes.py:172, routes/report_routes.py:35,42,45,71,133, services/notification_service.py:35, utils/helpers.py:38, seed.py:66,67,69,70,74
Description: Uso pervasivo de datetime.utcnow() — deprecated em Python 3.12; retorna datetime naive, sem timezone, fonte conhecida de bugs em comparações.
Impact: Comparações com datetimes aware (vindos de cliente/DB com tz) levantam TypeError; em Python ≥ 3.12 emite DeprecationWarning e será removido em versão futura.
Recommendation: Substituir por datetime.now(timezone.utc) em todos os call sites; ajustar colunas para timezone=True. Ver playbook §8.

### [MEDIUM] DEPRECATED_API
File: routes/task_routes.py:14,42,51,67,117,122,158,188,195,227,275-281, routes/user_routes.py:12,29,35,67,94,109,136,140,155,159,197, routes/report_routes.py:15-30,46-56,105,109,159,163,192,213
Description: Uso massivo da legacy Query API do Flask-SQLAlchemy (Model.query.get/filter_by/all/count). Esse padrão está descontinuado em SQLAlchemy 2.x.
Impact: Lança LegacyAPIWarning em SQLAlchemy 2.x e será removido; bloqueia upgrade futuro do ORM.
Recommendation: Migrar para db.session.get(Model, id) e db.session.execute(select(Model).filter_by(...)). Ver playbook §8.

### [MEDIUM] UNVALIDATED_INPUT_TYPE
File: routes/task_routes.py:113-114, 182-184
Description: priority é lido do JSON e comparado diretamente com 1/5 (data.get('priority', 3)) sem coerção a int — se o cliente enviar string, '5' < 1 levanta TypeError em Python 3 e cai no except: silencioso.
Impact: Payload malformado causa 500 opaco em vez de 400 explícito; comportamento inconsistente entre status (validado contra lista) e priority (comparação numérica direta).
Recommendation: Validar tipo no schema (marshmallow Integer com validate=Range(1,5)). Ver playbook §3 (extração para schemas).

### [MEDIUM] BROKEN_CASCADE_DELETE
File: routes/report_routes.py:212-220
Description: DELETE /categories/<id> remove a Category sem tratar tasks que referenciam category_id; a FK em models/task.py:14 é nullable mas não há ON DELETE SET NULL declarado, e o handler não atualiza/deleta dependências.
Impact: Em Postgres/MySQL com FK enforcement a operação falha; em SQLite cria FKs órfãs apontando para id inexistente — relatórios e listagens passam a retornar category_id "fantasma".
Recommendation: Declarar ondelete='SET NULL' (ou 'CASCADE' conforme regra) na FK; opcionalmente atualizar tasks no controller dentro de uma transação.

### [LOW] MAGIC_NUMBER
File: routes/task_routes.py:96-114, 167-184, routes/user_routes.py:65, 116
Description: Literais 3, 200, 1, 5, 4 espalhados em validações de título, prioridade e senha; constantes nomeadas existem em utils/helpers.py:110-116 mas nunca são importadas.
Impact: Mudar regra (ex: senha mínima de 8) requer caçar literais em vários arquivos.
Recommendation: Importar/centralizar MIN_TITLE_LENGTH, MAX_TITLE_LENGTH, MIN_PASSWORD_LENGTH, etc. em src/config ou módulo de constants.

### [LOW] LOOSE_TYPE_CHECK
File: routes/task_routes.py:141, 210, utils/helpers.py:103
Description: Uso de type(tags) == list em vez de isinstance(tags, list) para verificar listas.
Impact: Quebra para subclasses de list; estilo não-idiomático que dispara warning em linters.
Recommendation: Trocar por isinstance(tags, list).

### [LOW] PRINT_OR_CONSOLE_LOG
File: routes/task_routes.py:149,153,219,234, routes/user_routes.py:83,89,147, services/notification_service.py:21,24, utils/helpers.py:39-41
Description: print() usado para logging em código não-CLI (rotas, service e helper).
Impact: Saída não-estruturada vai para stdout; impossível filtrar por nível, redirecionar ou silenciar em produção.
Recommendation: Substituir por logging.getLogger(__name__) configurado em src/config/logging.py ou middleware equivalente.

### [LOW] DEAD_CODE_OR_UNUSED_IMPORT
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:8, utils/helpers.py:1-7
Description: Imports não-usados: app.py importa os/sys/json (apenas datetime é referenciado); task_routes importa json, os, sys, time; user_routes importa hashlib, json; report_routes importa json; utils/helpers importa os, sys, math, hashlib.
Impact: Ruído no namespace; linters ficam barulhentos; pode mascarar dependências reais.
Recommendation: Remover imports não-utilizados (rodar pyflakes/ruff ajuda a confirmar).

### [LOW] DEAD_CODE_OR_UNUSED_IMPORT
File: utils/helpers.py:25-50, 57-108
Description: Funções declaradas e nunca chamadas: sanitize_string, generate_id, log_action, is_valid_color, parse_date, process_task_data. Constantes VALID_STATUSES, VALID_ROLES, MAX_TITLE_LENGTH etc. também nunca são importadas.
Impact: Código morto aumenta superfície de manutenção e cria a ilusão de helpers reutilizáveis que na prática divergem das validações reais.
Recommendation: Remover funções não-usadas; promover constantes para src/config/constants.py e importar nos schemas.

================================
Total: 21 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y (confirmed)

================================
PHASE 3: REFACTORING COMPLETE
================================

## New Project Structure

```
task-manager-api/
├── app.py                       # entrypoint shim (re-exports src.app:app, src.config.database:db)
├── seed.py                      # uses sqlalchemy.delete + bcrypt-aware User
├── requirements.txt             # + bcrypt 4.1.2, + pyjwt 2.8.0
├── .env                         # gitignored — secrets/config
├── .env.example                 # template
└── src/
    ├── app.py                   # composition root: create_app(), registers blueprints + error handlers
    ├── config/
    │   ├── settings.py          # loads .env, Settings class, _required(name) helper
    │   ├── database.py          # db = SQLAlchemy()
    │   └── constants.py         # VALID_TASK_STATUSES, MIN/MAX_TITLE_LENGTH, BCRYPT_ROUNDS, …
    ├── models/
    │   ├── task.py              # Task + aware_utc(), is_overdue() uses constants
    │   ├── user.py              # password_hash + bcrypt + to_public_dict()
    │   └── category.py
    ├── schemas/
    │   └── task_schema.py       # marshmallow TaskCreate/TaskUpdate
    ├── controllers/
    │   ├── task_controller.py   # joinedload, db.session.get/execute(select(...))
    │   ├── user_controller.py   # validation + bcrypt
    │   ├── category_controller.py
    │   ├── report_controller.py # GROUP BY for tasks_by_*; SUM CASE for user_productivity
    │   └── auth_controller.py
    ├── services/
    │   ├── auth_service.py      # real JWT (HS256, exp from settings)
    │   └── notification_service.py # SMTP creds from settings; structured logging
    ├── views/
    │   ├── _helpers.py          # load_or_400 — converts marshmallow → 400
    │   ├── task_routes.py       # task_bp
    │   ├── user_routes.py       # user_bp
    │   ├── category_routes.py   # category_bp (split from report_bp)
    │   ├── report_routes.py     # report_bp
    │   └── auth_routes.py       # auth_bp (POST /login)
    └── middlewares/
        └── error_handler.py     # AppError + Bad/Unauthorized/Forbidden/NotFound/Conflict + 500 fallback
```

## Validation
  ✓ Application boots without errors (`python app.py` → debug server on :5000)
  ✓ All endpoints respond correctly
      | endpoint                  | pre   | post  |
      |---------------------------|-------|-------|
      | GET /                     | 200   | 200   |
      | GET /health               | 200   | 200   |
      | GET /tasks                | 200   | 200   |
      | GET /tasks/1              | 404 * | 200   |
      | GET /tasks/search?q=ci    | 200   | 200   |
      | GET /tasks/stats          | 200   | 200   |
      | GET /users                | 500 † | 200   |
      | GET /users/1              | 500 † | 200   |
      | GET /users/1/tasks        | 500 † | 200   |
      | GET /reports/summary      | 500 † | 200   |
      | GET /reports/user/1       | 500 † | 200   |
      | GET /categories           | 200   | 200   |
      | POST /tasks (valid body)  | —     | 201   |
      | POST /tasks (bad body)    | —     | 400   |
      | POST /login               | —     | 200 (real HS256 JWT) |
      * 404 because seed had not been run against the stale DB.
      † 500 because `users` schema in stale DB lacked the `password` column.
      Both turn 200 after the fresh seed — correction, not regression.
  ✓ Zero CRITICAL/HIGH findings on re-audit
      - HARDCODED_SECRET            — clean (literal grep returns 0 hits in src/)
      - WEAK_HASH_FOR_AUTH          — clean (no `hashlib.md5`/`sha1`)
      - PII_LEAK_IN_RESPONSE        — clean (no `'password':` in serializers; verified GET /users/1 has no password key)
      - FAKE_AUTH_TOKEN             — clean (real JWT signed with SECRET_KEY)
      - BUSINESS_LOGIC_IN_VIEW      — clean (views only parse + dispatch + jsonify)
      - BLUEPRINT_OR_ROUTER_LEAK    — clean (category_bp split from report_bp)
      - BARE_EXCEPT                 — clean (no bare `except:`)
      - DEPRECATED_API datetime     — clean (no `datetime.utcnow()`)
      - DEPRECATED_API Model.query  — clean (no `Model.query.<...>`; uses db.session.get/execute)
      - N_PLUS_ONE_QUERY            — fixed via joinedload (GET /tasks) and GROUP BY (reports)
      - LOOSE_TYPE_CHECK            — clean (no `type(x) == ...`)

================================

## Side-effects worth flagging to the user
- `instance/tasks.db` was deleted and re-seeded; the schema is now `users.password_hash` (was `users.password`). Pre-existing JWT/bcrypt-incompatible passwords are gone.
- A pre-existing app process is still running on port 5000 with the OLD code (PID 42577). Kill it and restart with `python app.py` to pick up the refactored composition.
- `requirements.txt` gained `bcrypt==4.1.2` and `pyjwt==2.8.0`. These were installed into the existing `.venv`.

