================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2 + sqlite3 5.1.6 (in-memory)
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 3 | HIGH: 7 | MEDIUM: 4 | LOW: 3

## Findings

### [CRITICAL] HARDCODED_SECRET
File: src/utils.js:1-7
Description: Objeto `config` exporta `dbPass`, `paymentGatewayKey` (formato `pk_live_*` — chave de produção de gateway), `smtpUser` e `dbUser` como literais no código. Já existe um `.env` no projeto com `PAYMENT_GATEWAY_KEY` etc., mas o código nunca o lê.
Impact: Credenciais reais comitadas no repo; rotação exige patch + redeploy. Qualquer pessoa com acesso ao repo (incluindo histórico) tem as chaves.
Recommendation: Mover para `.env` (já existe um) e ler via `process.env` em `src/config/settings.js`. Adicionar `.env.example` sem valores. Ver playbook §1.

### [CRITICAL] PLAINTEXT_PASSWORD
File: src/AppManager.js:12,18
Description: Tabela `users` declara coluna `pass TEXT` (sem sufixo `_hash`) e o seed insere a senha `'123'` em plaintext direto na tabela. Login (não há, mas o schema permanece) compararia o valor cru.
Impact: Vazamento do banco = vazamento direto das senhas; CWE-256.
Recommendation: Renomear coluna para `password_hash`, gerar bcrypt no seed e em todos os INSERTs de usuário. Ver playbook §5.

### [CRITICAL] WEAK_HASH_FOR_AUTH
File: src/utils.js:17-23
Description: Função caseira `badCrypto` faz 10000 iterações concatenando `Buffer.from(pwd).toString('base64').substring(0, 2)` e retorna apenas 10 caracteres. Não é hash criptográfico — é determinístico, sem salt, com colisões triviais e espaço de saída minúsculo. Usada em `src/AppManager.js:68` para criar usuários.
Impact: Senhas efetivamente em texto claro recuperável; equivale a não ter hash.
Recommendation: Substituir por `bcrypt.hash(pwd, 12)` / `bcrypt.compare`. Ver playbook §5.

### [HIGH] GOD_FILE_OR_CLASS
File: src/AppManager.js:1-141
Description: Classe única `AppManager` concentra schema do DB, seeding, todas as 3 rotas (checkout, financial-report, delete user), regra de pagamento, gravação de audit log e cache. Mistura quatro domínios (users, courses, enrollments+payments, auditing).
Impact: Impossível testar em isolamento; qualquer mudança em uma rota propaga risco às outras; não escala para mais entidades.
Recommendation: Quebrar em `models/{userModel,courseModel,enrollmentModel,paymentModel,auditModel}.js`, `controllers/{checkoutController,reportController,userController}.js`, `views/*Routes.js` e `services/paymentService.js`. Ver playbook §2.

### [HIGH] CALLBACK_HELL
File: src/AppManager.js:28-78
Description: Handler de `POST /api/checkout` aninha 5 níveis de callbacks de `db.get`/`db.run`, com tratamento de erro replicado em cada nível e closure `processPaymentAndEnroll` declarada no meio do fluxo.
Impact: Fluxo ilegível; tratamento de erro inconsistente (alguns níveis não logam); risco de "resposta dupla" e leaks de connection se um callback intermediário falhar silenciosamente.
Recommendation: `util.promisify` no sqlite3 + `async/await` no controller, com erros customizados subindo para middleware. Ver playbook §6.

### [HIGH] CALLBACK_HELL
File: src/AppManager.js:80-129
Description: Handler de `GET /api/admin/financial-report` faz fan-out manual com contadores `coursesPending`/`enrPending` para coordenar callbacks aninhados de `db.all` em courses → enrollments → users → payments.
Impact: Lógica de coordenação manual é frágil e quase impossível de auditar; basta um callback errado decrementar duas vezes para o `res.json` nunca disparar (request pendurado) ou disparar duas vezes.
Recommendation: Reescrever com `async/await` + uma única query com JOIN (ver §9). Ver playbook §6.

### [HIGH] BUSINESS_LOGIC_IN_VIEW
File: src/AppManager.js:43-64
Description: O handler de rota decide o status do pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`), faz find-or-create de usuário, insere enrollment, payment, audit log e atualiza cache — tudo dentro do callback de rota.
Impact: Regras de negócio acopladas ao Express; não-reutilizáveis e impossíveis de testar sem subir HTTP.
Recommendation: Extrair para `controllers/checkoutController.js` (orquestração) + `services/paymentService.js` (regra do gateway). View só faz parse + serialização. Ver playbook §3.

### [HIGH] SECRET_LEAK_IN_LOGS
File: src/AppManager.js:45
Description: `console.log` registra **número do cartão** (`cc`) e **chave de produção do gateway** (`config.paymentGatewayKey`) a cada checkout.
Impact: Vazamento de PCI + credencial em qualquer log aggregator (CloudWatch, stdout em container, Sentry breadcrumbs). Violação direta de PCI-DSS.
Recommendation: Remover o log. Logs estruturados não devem conter PAN nem chaves; aplicar redaction se logging for necessário para audit.

### [HIGH] BROKEN_CASCADE_DELETE
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` apaga só o usuário. Schema (linhas 12-15) não declara FK nem `ON DELETE CASCADE`. A própria mensagem de resposta admite o problema: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`.
Impact: Dados órfãos em `enrollments` e `payments`; relatório financeiro retorna `student: 'Unknown'` para enrollments cujo user_id não existe mais.
Recommendation: Declarar FKs com `ON DELETE CASCADE` no schema, ou deletar enrollments+payments+audit em transação no controller.

### [HIGH] GLOBAL_MUTABLE_STATE
File: src/utils.js:9-10,25
Description: `let globalCache = {}` e `let totalRevenue = 0` no escopo do módulo, exportados e mutáveis. `logAndCache` (linha 12) escreve em `globalCache` a cada checkout.
Impact: Memory leak (cache cresce sem bound), race conditions sob concorrência, testes acoplados a estado global.
Recommendation: Mover cache para serviço instanciado pelo composition root (DI), com TTL/limite. Remover `totalRevenue` (dead — nunca atualizado). Ver playbook §11.

### [MEDIUM] N_PLUS_ONE_QUERY
File: src/AppManager.js:80-129
Description: Para cada course faz `db.all` de enrollments; para cada enrollment faz `db.get` de user e `db.get` de payment. Resulta em `1 + N + 2*M` queries.
Impact: Latência cresce linearmente com número de courses × enrollments; em produção real (Postgres + RTT) o relatório vira inviável a partir de algumas centenas de matrículas.
Recommendation: Substituir por uma única query com `LEFT JOIN` entre courses, enrollments, users e payments, e agrupar em memória. Ver playbook §9.

### [MEDIUM] BARE_EXCEPT_OR_SWALLOWED_ERROR
File: src/AppManager.js:38,41,51,55,84,133
Description: Cada callback de `db.*` retorna `res.status(500).send("Erro DB" / "Erro Matrícula" / "Erro Pagamento")` sem logar `err`. Em `:38` o erro é mascarado como `404`. Em `:133` o erro do DELETE é totalmente ignorado (`(err) => { res.send(...) }` sem checagem).
Impact: Falhas silenciosas em produção; impossível diagnosticar incidente sem reproduzir local.
Recommendation: Centralizar em middleware `errorHandler` (registrado por último em `app.js`); controllers levantam exceções customizadas (`NotFoundError`, `PaymentDeniedError`). Ver playbook §7.

### [MEDIUM] MISSING_CASCADE_OR_TRANSACTION
File: src/AppManager.js:50-62
Description: Sequência `INSERT enrollment → INSERT payment → INSERT audit_log` ocorre em callbacks separados sem `BEGIN`/`COMMIT`. Se a inserção do payment falhar após enrollment criado, a matrícula permanece sem pagamento associado; se audit falhar, ainda assim retorna 200.
Impact: Estado parcial — usuário matriculado sem registro financeiro, ou pagamento sem audit. Reconciliação manual.
Recommendation: Envolver as 3 escritas em `BEGIN ... COMMIT`/`ROLLBACK` (sqlite3 suporta `db.serialize` + `db.run("BEGIN")`). Ver playbook §12.

### [MEDIUM] UNVALIDATED_INPUT_TYPE
File: src/AppManager.js:29-35
Description: `req.body.usr/eml/pwd/c_id/card` são consumidos diretamente sem validação de tipo. `cc.startsWith("4")` (linha 46) crasharia se `card` vier como número JSON; `cid` é interpolado em SQL sem coerção a inteiro (placeholder protege contra injection mas não contra payload do tipo `{c_id: {"$ne": null}}` se o driver mudar).
Impact: 500 não-tratado em payloads malformados; comportamento indefinido.
Recommendation: Validar shape e tipos no edge com `zod`/`joi` antes de chamar o controller. Renomear campos cifrados (`usr`/`eml`/`pwd`) para `name`/`email`/`password` enquanto refatora.

### [LOW] DEAD_CODE_OR_UNUSED_IMPORT
File: src/utils.js:10,25 ; src/AppManager.js:2
Description: `totalRevenue` é declarada e exportada em `utils.js` mas nunca atribuída em lugar algum; `AppManager.js:2` faz destructuring de `totalRevenue` mas também não usa.
Impact: Confunde leitor (sugere lógica de receita acumulada que não existe); aumenta superfície de manutenção.
Recommendation: Remover a variável e o import.

### [LOW] PRINT_OR_CONSOLE_LOG
File: src/utils.js:13 ; src/app.js:13
Description: `console.log` em `logAndCache` (utility) e no boot do servidor. O do boot é tolerável, mas o de utility deveria estar em logger configurável.
Impact: Logs não-estruturados, sem nível, sem timestamp; difícil filtrar em produção.
Recommendation: Trocar por `pino`/`winston` configurado em `config/logger.js`. Manter apenas o log de boot (idealmente também via logger).

### [LOW] INADEQUATE_HTTP_STATUS
File: src/AppManager.js:38,48,135
Description: (a) Linha 38 retorna `404` mesmo quando `err` é setado (deveria distinguir 500 de 404). (b) Linha 48 retorna `400 Bad Request` para "Pagamento recusado" — `402 Payment Required` é o status semântico correto. (c) Linha 135 retorna `200` por padrão mesmo quando o DELETE falha (deveria 500/204).
Impact: Clientes não conseguem distinguir falha do servidor de erro de domínio; observabilidade prejudicada.
Recommendation: Mapear corretamente: `402` para pagamento recusado, `500` para erro de DB, `204` para DELETE sucesso. Ver RFC 7231/9110.

================================
Total: 17 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
