================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3 + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 5 | HIGH: 6 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] HARDCODED_SECRET
File: app.py:7
Description: SECRET_KEY do Flask hardcoded ("minha-chave-super-secreta-123") no código-fonte; também `DEBUG=True` em produção (linha 8).
Impact: Segredo commitado no repo expõe sessões e CSRF tokens; rotação requer mudar código + redeploy. Debug ligado vaza stack traces.
Recommendation: Mover para `.env` e ler via `os.environ`; gerar uma nova chave (a antiga está comprometida). Ver playbook §1.

### [CRITICAL] SQL_INJECTION_STRING_CONCAT
File: models.py:28,48-50,57-61,68,92,126-129,140,148-166,174,188,192,206,220,224,280,289-297
Description: Praticamente todas as queries em `models.py` são construídas via `+ str(...)` com input do usuário — SELECT, INSERT, UPDATE, DELETE. Inclui buscar_produtos (linhas 289-297) que concatena dinamicamente filtros LIKE/categoria recebidos por querystring.
Impact: Injeção arbitrária de SQL em todos os endpoints de produto/usuário/pedido — vetor direto de extração ou modificação do banco.
Recommendation: Substituir por placeholders `?` parametrizados em todas as chamadas; para filtros opcionais, montar lista de placeholders + lista de params, nunca string. Ver playbook §4.

### [CRITICAL] PLAINTEXT_PASSWORD
File: database.py:31,75-83 + models.py:109-120,122-131
Description: Schema declara coluna `senha TEXT` (database.py:31) e seed grava "admin123"/"123456" em texto puro (database.py:75-83); login compara `WHERE email = ? AND senha = ?` literal (models.py:109-111) e get_todos_usuarios/get_usuario_por_id retornam `senha` no payload.
Impact: Vazamento do DB = vazamento de credenciais reais; login é também SQL-injection (combo com finding anterior) → bypass trivial. CWE-256.
Recommendation: Substituir coluna por `password_hash` com bcrypt (cost ≥ 12); re-seedar com hash; remover senha de qualquer serializer. Ver playbook §5 e §10.

### [CRITICAL] ARBITRARY_SQL_ENDPOINT
File: app.py:59-78
Description: Endpoint `POST /admin/query` aceita um campo `sql` no body e o passa direto para `cursor.execute`, sem auth, sem validação, sem allow-list.
Impact: Equivalente a dar acesso shell ao banco — qualquer cliente pode `DROP TABLE`, exfiltrar dados, ou alterar registros.
Recommendation: Remover o endpoint. Se precisar de operações administrativas, expor rotas específicas com schema fechado e auth de admin. Endpoint `/admin/reset-db` (app.py:47-57) também precisa de auth.

### [CRITICAL] PII_LEAK_IN_RESPONSE
File: models.py:72-87,89-103
Description: `get_todos_usuarios` e `get_usuario_por_id` constroem dict incluindo o campo `senha` (texto puro), exposto via `GET /usuarios` e `GET /usuarios/<id>`.
Impact: Endpoint público vaza credenciais de todos os usuários cadastrados — qualquer cliente da API obtém senhas em texto plano.
Recommendation: Allow-list de campos públicos (`id, nome, email, tipo, criado_em`); centralizar em `to_public_dict()`. Ver playbook §10.

### [HIGH] GOD_FILE_OR_CLASS
File: models.py:1-314
Description: Arquivo único contém persistência de 4 entidades (produtos, usuários, pedidos, itens_pedido) + lógica de relatório de vendas + regras de desconto (linhas 256-262).
Impact: Impossível testar em isolamento; mudanças em uma entidade quebram outras; alto acoplamento.
Recommendation: Separar em `src/models/{produto,usuario,pedido}_model.py`; mover regras de desconto/relatório para `src/services/relatorio_service.py`. Ver playbook §2.

### [HIGH] GOD_FILE_OR_CLASS
File: controllers.py:1-292
Description: Arquivo único contém todos os handlers HTTP de 4 domínios + validação + side-effects de notificação (linhas 208-210, 248-250) + leitura/escrita direta de DB no health_check (linhas 264-292).
Impact: View misturada com controller misturada com service; violação completa do MVC.
Recommendation: Separar em `src/views/{produto,usuario,pedido}_routes.py` (apenas roteamento) + `src/controllers/{produto,usuario,pedido}_controller.py` (orquestração). Ver playbook §2 e §3.

### [HIGH] BUSINESS_LOGIC_IN_VIEW
File: controllers.py:24-62,64-96,237-255,188-220
Description: Handlers de rota fazem (a) validação de range/whitelist (`if preco < 0`, `if categoria not in [...]`, `if novo_status not in [...]`), (b) emitem "notificações" via `print` simulando email/SMS/push (criar_pedido, atualizar_status_pedido), (c) decidem ramo de fluxo no handler.
Impact: Lógica não-reutilizável; impossível testar regra sem subir HTTP; notificações não são serviço — são log.
Recommendation: Extrair validação para `controllers/`/schema (pydantic/marshmallow); mover envio de notificação para `services/notification_service.py`. Ver playbook §3.

### [HIGH] SECRET_LEAK_IN_RESPONSE_HEALTH
File: controllers.py:264-292
Description: Endpoint `GET /health` retorna `secret_key`, `debug`, `db_path` e contagens de tabelas no payload.
Impact: Endpoint geralmente público (load balancers, monitoring) vaza segredo da app a qualquer scanner; expõe caminho de DB no filesystem.
Recommendation: Health = `{ status, version }`. Nada mais. Mover counts para um endpoint admin autenticado se necessário.

### [HIGH] GLOBAL_MUTABLE_STATE
File: database.py:4-12
Description: `db_connection = None` no nível do módulo, mutado em `get_db()` com lazy init e `check_same_thread=False`.
Impact: Race conditions sob concorrência (sqlite3 single connection compartilhada entre threads); testes acoplados a estado de módulo; impossível resetar entre suites.
Recommendation: Conexão por request via `flask.g` + `teardown_appcontext`. Ver playbook §11.

### [HIGH] BROKEN_CASCADE_DELETE
File: models.py:65-70 + database.py:36-53
Description: `deletar_produto` faz `DELETE FROM produtos WHERE id = ?` sem remover `itens_pedido` que referenciam o produto; schema das tabelas `pedidos` e `itens_pedido` não declara FK nem `ON DELETE CASCADE`.
Impact: Itens de pedido órfãos apontando para produtos inexistentes; relatórios de vendas inconsistentes; `get_pedidos_usuario` mostra "Desconhecido" para produto deletado (linha 196).
Recommendation: Declarar FK com `ON DELETE CASCADE` no schema, ou exclusão programática em transação (delete itens → delete produto). Migrar `loja.db` ou recriá-lo.

### [MEDIUM] N_PLUS_ONE_QUERY
File: models.py:171-201,203-233
Description: `get_pedidos_usuario` e `get_todos_pedidos` fazem 1 query para buscar pedidos, depois 1 query por pedido para buscar itens, depois 1 query por item para buscar nome do produto. 1 + N + N*M.
Impact: Latência cresce linearmente com volume; relatório/listagens degradam em produção.
Recommendation: Single query com JOIN entre `pedidos`, `itens_pedido` e `produtos`, agrupar em memória. Ver playbook §9.

### [MEDIUM] MISSING_CASCADE_OR_TRANSACTION
File: models.py:133-169
Description: `criar_pedido` faz INSERT em `pedidos`, INSERT em `itens_pedido` (loop) e UPDATE em `produtos.estoque` (loop) sem `BEGIN`/`COMMIT` explícito; falha no meio deixa pedido sem itens ou estoque dessincronizado.
Impact: Estado parcial em caso de falha — pedido criado mas itens não, ou estoque debitado sem pedido.
Recommendation: Envolver em transação (`db.execute("BEGIN")` + `db.commit()` em try/except com `rollback`); usar `UPDATE ... WHERE estoque >= ?` para evitar race em estoque negativo. Ver playbook §12.

### [MEDIUM] DUPLICATE_VALIDATION_LOGIC
File: controllers.py:24-62,64-96
Description: `criar_produto` e `atualizar_produto` repetem o mesmo bloco de validação (campos obrigatórios, preco/estoque ≥ 0, len(nome)) com diferenças triviais.
Impact: Drift assimétrico (atualizar_produto NÃO valida `len(nome)` nem categoria); bug latente.
Recommendation: Extrair schema (pydantic/marshmallow) ou função `validate_produto_payload(data)` reutilizada por ambos.

### [MEDIUM] BARE_EXCEPT_OR_SWALLOWED_ERROR
File: controllers.py:10-12,21-22,60-62,95-96,108-109,125-126,133-134,143-144,164-165,185-186,218-220,226-227,234-235,254-255,261-262,290-292
Description: Quase todo handler termina com `except Exception as e: return jsonify({"erro": str(e)}), 500` — captura genérica, sem log estruturado, retorna a mensagem da exception (que pode conter detalhes do schema do DB).
Impact: Bugs silenciosos em produção; mensagens de erro vazam detalhes internos; impossível distinguir 4xx de 5xx no client.
Recommendation: Centralizar em `middlewares/error_handler.py` com hierarquia de exceptions custom (NotFoundError → 404, ValidationError → 400, AppError → genérico); logar com stack trace. Ver playbook §7.

### [MEDIUM] UNVALIDATED_INPUT_TYPE
File: controllers.py:39-46,82-90,118-121,195-201,239-243
Description: `preco`/`estoque` lidos do JSON e comparados com `< 0` sem coerção (`int(...)`/`float(...)`); `usuario_id` em criar_pedido idem; querystring `preco_min`/`preco_max` é convertido com `float()` mas sem try/except (linha 119).
Impact: Crash 500 com payload malformado (TypeError em `< 0`); ou comparação string vs int silenciosamente errada (`"-1" < 0` é False em str).
Recommendation: Schema validation no edge (pydantic/marshmallow); rejeitar com 400 antes de chegar no model.

### [LOW] MAGIC_NUMBER
File: controllers.py:47-50,87-90 + models.py:257-262
Description: Literais `2`, `200` para limites de nome de produto; tiers de desconto `10000`, `5000`, `1000` com percentuais `0.1`, `0.05`, `0.02` no `relatorio_vendas`.
Recommendation: Mover para constantes nomeadas em `src/config/constants.py` ou variáveis de ambiente.

### [LOW] DEAD_CODE_OR_UNUSED_IMPORT
File: models.py:2
Description: `import sqlite3` em models.py sem uso — sqlite3 só é referenciado em database.py.
Recommendation: Remover.

### [LOW] PRINT_OR_CONSOLE_LOG
File: controllers.py:8,11,57,61,106,161,179,182,208-210,219,248,250 + app.py:56,83-86 + database.py (n/a)
Description: Múltiplos `print(...)` substituindo logging estruturado: contagens de listagem, erros, "ENVIANDO EMAIL/SMS/PUSH" simulando notificações.
Recommendation: `logging` configurado em `config/`, com níveis (info/warn/error) e handler estruturado. Notificações fake devem virar `services/notification_service.py`.

### [LOW] INADEQUATE_HTTP_STATUS
File: controllers.py (handlers de exception, ex: linhas 11-12,60-62)
Description: Qualquer falha vira `500 {"erro": str(e)}`, inclusive ValidationError do payload (deveria ser 400) ou produto não encontrado em fluxos sem o early-return de 404.
Recommendation: Mapear exceptions específicas para status corretos (404, 400, 409, 422) via middleware §7.

================================
Total: 20 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
