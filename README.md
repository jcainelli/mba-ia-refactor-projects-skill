# Criação de Skills — Refatoração Arquitetural Automatizada

O projeto apresenta a Skill `/refactor-arch` que audita e refatora qualquer codebase para o padrão MVC de forma agnóstica de tecnologia.

Os requisitos implementados são parte do desafio técnico do MBA Engenharia de Software com IA da FullCycle. O arquivo [README_rules.md](/README_rules.md), detalha as regras gerais do desafio.

Nesta versão da Skill, ela está preparada para executar as seguintes fases sequênciais: 

   1. **Fase 1** — Análise: Detectar stack, mapear arquitetura atual, imprimir resumo
   2. **Fase 2** — Auditoria: Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
   3. **Fase 3** — Refatoração: Reestruturar para o padrão MVC, validar que funciona
   
O repositório também contém 3 projetos para validação da Skill:
   1. `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
   2. `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
   3. `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade


## Tecnologias
   * Claude Code

## Análise Manual
 Listagem de problemas identificados durante pré criação da Skill, classificados por severidade e justificativa de por que cada problema é relevante.
   
   1. `code-smells-project/`
      | Problema | Justificativa | Severidade |
      |----------|---------------|------------|
      | GET /usuarios e GET /usuarios/<id> retornam o campo senha no payload (models.py:79-103)| Endpoint público expondo credenciais em texto plano de todos os usuários cadastrados — vazamento direto via API, sem nem precisar comprometer o DB.| CRITICAL |
      | controllers.py (292 LOC, todos os handlers HTTP + validação + notificações fake + acesso direto a DB no /health)| View, controller e service estão grudados num único arquivo — sem separação de responsabilidades, refactors locais propagam      globalmente.| HIGH |
      | Validação duplicada (e divergente) entre criar_produto e atualizar_produto (controllers.py:24-96)| atualizar_produto NÃO valida len(nome) nem categoria — drift assimétrico significa que regras valem para criação mas não para atualização (bug latente).| MEDIUM |
      | except Exception as e: return jsonify({"erro": str(e)}), 500 em todos os handlers| Captura genérica sem log estruturado; vaza detalhes internos do schema/banco no body do response 500; impossível distinguir 4xx de 5xx no client.| MEDIUM |
      | Números mágicos para limites e tiers de desconto (controllers.py:47-50,87-90, models.py:257-262)| Valores 2, 200, 10000/5000/1000, 0.1/0.05/0.02 espalhados sem nome — mudança de regra exige caçar literais; difícil documentar a intenção.| LOW |
      | import sqlite3 não-utilizado em models.py:2| Dead code mascara dependências reais; sinaliza falta de higiene mínima do módulo.| LOW |

   2. `ecommerce-api-legacy/`
      | Problema | Justificativa | Severidade |
      |----------|---------------|------------|
      | `PLAINTEXT_PASSWORD` — coluna `pass TEXT` e seed `'123'` em `src/AppManager.js:12,18` | Vazamento do banco= vazamento direto de senhas; CWE-256. | CRITICAL |
      | `BARE_EXCEPT_OR_SWALLOWED_ERROR` em `src/AppManager.js:38,41,51,55,84,133` — `res.status(500).send("ErroDB")` sem log; linha 38 mascara DB-error como 404; linha 133 ignora `err` totalmente | Falhas silenciosas emprodução; impossível diagnosticar incidente. | MEDIUM |
      | `WEAK_HASH_FOR_AUTH` — função `badCrypto` em `src/utils.js:17-23` (loop base64 + substring de 10 chars) |Determinística, sem salt, espaço de saída minúsculo — equivale a não ter hash. | CRITICAL |
      | `DEAD_CODE_OR_UNUSED_IMPORT` — `totalRevenue` declarado/exportado/importado em `src/utils.js:10,25` e`src/AppManager.js:2` mas nunca atribuído | Sugere lógica de receita acumulada que não existe; aumenta superfíciemorta. | LOW | 
      | `PRINT_OR_CONSOLE_LOG` em `src/utils.js:13` (logAndCache) e `src/app.js:13` (boot) | Logs não-estruturados,sem nível/timestamp; difícil filtrar em produção. | LOW |

   3. `task-manager-api/`
      | Problema | Justificativa | Severidade |
      |----------|---------------|------------|
      | models/user.py:16-25 (to_dict() expondo password) | Exposição de dados sensíveis | CRITICAL |
      | BUSINESS_LO`GIC_IN_VIEW — routes/task_routes.py:11-298 (validação + regra + persistência no handler) | Lógica centralizada | HIGH |
      | DEAD_CODE_OR_UNUSED_IMPORT — imports não-usados em app.py:7, routes/task_routes.py:7, routes/user_routes.py:6, routes/report_routes.py:8, utils/helpers.py:1-7 | Pastas legadas (models/, routes/,services/, utils/, database.py) deletadas; arquivos novos só importam o que usam; único # noqa: F401 em src/app.py é intencional (registra mappers SQLAlchemy) | LOW |
      | DEAD_CODE_OR_UNUSED_IMPORT — funções/constantes mortas em utils/helpers.py:25-50, 57-108 | Arquivo deletado; constantes úteis (VALID_TASK_STATUSES, VALID_USER_ROLES etc.) migradas parasrc/config/constants.py e efetivamente importadas em schemas/controllers | LOW |
      | MAGIC_NUMBER — routes/task_routes.py:96-114, 167-184 + routes/user_routes.py:65, 116 | Dificuldade em panutenções futuras | LOW |
      
   
## Construção da Skill
A skill refactor-arch segue um pipeline rígido de três fases (análise, auditoria com pausa obrigatória pro humano, refatoração com validação via curl pré/pós) e separa conhecimento em cinco arquivos de referência pra manter o SKILL.md como índice e permitir iterar nos detalhes sem reescrever a skill. O catálogo cobre anti-patterns que aparecem nos três projetos mas são universais — SQL injection, hardcoded secrets, plaintext/weak hash, PII leak (CRITICAL), god class, callback hell, fake JWT (HIGH), N+1 e bare except (MEDIUM), magic numbers (LOW) e detecção de APIs depreciadas. 
  
A agnosticidade veio de listar signals equivalentes em Python e Node lado a lado em cada anti-pattern e de detectar a stack na Fase 1 antes de aplicar qualquer transformação. 

Os dois maiores desafios foram o Project 3, que já era parcialmente em camadas e exigiu classificar arquitetura em três níveis pra promover o existente em vez de reescrever (preservando contratos das rotas), e garantir idempotência — rodar a skill duas vezes tem que dar zero findings na segunda, o que forçou o snapshot com curl pra pegar regressões silenciosas antes de declarar sucesso.

## Seção "Resultados"

   1. **code-smell-project**

      <details>
         <summary>Resultados - code-smell-project</summary>

            ================================                                    
            PHASE 1: PROJECT ANALYSIS                                             
            ================================                                      
            Language:       Python 3                                  
            Framework:      Flask 3.1.1                                           
            Dependencies:   flask==3.1.1, flask-cors==5.0.1, sqlite3 (stdlib)     
            Domain:         E-commerce API (produtos, usuarios, pedidos,
            itens_pedido)                                                         
            Architecture:   monolithic-flat — 4 arquivos .py na raiz,           
            rotas+queries+validações misturadas
            Source files:   4 files analyzed (~780 LOC)
            DB tables:      produtos, usuarios, pedidos, itens_pedido
            Run command:    python app.py
            ================================

            ================================                          
            PHASE 2: ARCHITECTURE AUDIT REPORT
            ================================                                      
            Project: code-smells-project
            Stack:   Python 3 + Flask 3.1.1                                       
            Files:   4 analyzed | ~780 lines of code                            

            ## Summary
            CRITICAL: 5 | HIGH: 6 | MEDIUM: 5 | LOW: 4

            ## Findings

            ### [CRITICAL] HARDCODED_SECRET
            File: app.py:7
            Description: SECRET_KEY do Flask hardcoded
            ("minha-chave-super-secreta-123") no código-fonte; também `DEBUG=True`
            em produção (linha 8).
            Impact: Segredo commitado no repo expõe sessões e CSRF tokens; rotação
            requer mudar código + redeploy. Debug ligado vaza stack traces.
            Recommendation: Mover para `.env` e ler via `os.environ`; gerar uma
            nova chave (a antiga está comprometida). Ver playbook §1.
                                 
            ### [CRITICAL] SQL_INJECTION_STRING_CONCAT
            File: models.py:28,48-50,57-61,68,92,126-129,140,148-166,174,188,192,2
            06,220,224,280,289-297                 
            Description: Praticamente todas as queries em `models.py` são         
            construídas via `+ str(...)` com input do usuário — SELECT, INSERT,
            UPDATE, DELETE. Inclui buscar_produtos (289-297) que concatena        
            dinamicamente filtros LIKE/categoria recebidos por querystring.     
            Impact: Injeção arbitrária de SQL em todos os endpoints de            
            produto/usuário/pedido — vetor direto de extração ou modificação do 
            banco.                                                                
            Recommendation: Substituir por placeholders `?` parametrizados em   
            todas as chamadas; para filtros opcionais, montar lista de            
            placeholders + lista de params, nunca string. Ver playbook §4.      
                                                                           
            ### [CRITICAL] PLAINTEXT_PASSWORD                      
            File: database.py:31,75-83 + models.py:109-120,122-131                
            Description: Schema declara `senha TEXT` e seed grava                 
            "admin123"/"123456" em texto puro; login compara `WHERE email = ? AND
            senha = ?` literal e get_todos_usuarios/get_usuario_por_id retornam   
            `senha` no payload.                                                   
            Impact: Vazamento do DB = vazamento de credenciais; combinado com SQLi
            do login → bypass trivial. CWE-256.                                  
            Recommendation: Coluna `password_hash` com bcrypt (cost ≥ 12);        
            re-seedar com hash; remover senha de qualquer serializer. Ver playbook
            §5 e §10.                                                            
                                                                           
            ### [CRITICAL] ARBITRARY_SQL_ENDPOINT                                 
            File: app.py:59-78         
            Description: Endpoint `POST /admin/query` aceita um campo `sql` no    
            body e o passa direto para `cursor.execute`, sem auth, sem validação.
            Impact: Equivalente a dar acesso shell ao banco — qualquer cliente    
            pode `DROP TABLE`, exfiltrar dados.                                   
            Recommendation: Remover o endpoint. `/admin/reset-db` (47-57) também
            precisa de auth.                                                      
                                                                           
            ### [CRITICAL] PII_LEAK_IN_RESPONSE    
            File: models.py:72-87,89-103                                          
            Description: `get_todos_usuarios` e `get_usuario_por_id` constroem  
            dict incluindo o campo `senha`, exposto via `GET /usuarios` e `GET    
            /usuarios/<id>`.                                                    
            Impact: Endpoint público vaza credenciais de todos os usuários        
            cadastrados em texto plano.                                         
            Recommendation: Allow-list de campos públicos via `to_public_dict()`. 
            Ver playbook §10.                                                     
                                                                           
            ### [HIGH] GOD_FILE_OR_CLASS                                          
            File: models.py:1-314                                                 
            Description: Arquivo único contém persistência de 4 entidades + lógica
            de relatório de vendas + regras de desconto (256-262).               
            Impact: Impossível testar em isolamento; mudanças propagam.         
            Recommendation: Separar em                                            
            `src/models/{produto,usuario,pedido}_model.py`; mover relatório para
            `src/services/relatorio_service.py`. Playbook §2.                     
                                                                           
            ### [HIGH] GOD_FILE_OR_CLASS                                          
            File: controllers.py:1-292                                            
            Description: Arquivo único contém todos os handlers HTTP de 4 domínios
            + validação + side-effects de notificação (208-210, 248-250) +       
            leitura/escrita direta de DB no health_check.                         
            Impact: View misturada com controller misturada com service; violação
            completa do MVC.                                       
            Recommendation: Separar em `src/views/*_routes.py` (roteamento) +     
            `src/controllers/*_controller.py` (orquestração). Playbook §2 e §3.   
                                                                           
            ### [HIGH] BUSINESS_LOGIC_IN_VIEW                                     
            File: controllers.py:24-62,64-96,237-255,188-220                      
            Description: Handlers fazem validação de range/whitelist, emitem
            "notificações" via print simulando email/SMS/push, decidem ramo de    
            fluxo no handler.                                                   
            Impact: Lógica não-reutilizável; impossível testar regra sem subir    
            HTTP.                                                               
            Recommendation: Extrair validação para schema; mover notificação para 
            `services/notification_service.py`. Playbook §3.                      
                                                                           
            ### [HIGH] SECRET_LEAK_IN_RESPONSE_HEALTH                             
            File: controllers.py:264-292                                          
            Description: `GET /health` retorna `secret_key`, `debug`, `db_path` no
            payload.                                                             
            Impact: Endpoint público vaza segredo da app a qualquer scanner; expõe
            caminho de DB.                                                       
            Recommendation: Health = `{ status, version }`. Counts em endpoint  
            admin autenticado.                                                    
                                                                           
            ### [HIGH] GLOBAL_MUTABLE_STATE
            File: database.py:4-12                                                
            Description: `db_connection = None` no nível do módulo, mutado em   
            `get_db()` com `check_same_thread=False`.                             
            Impact: Race conditions sob concorrência; testes acoplados a estado de
            módulo.                                                              
            Recommendation: Conexão por request via `flask.g` +                 
            `teardown_appcontext`. Playbook §11.                                  
                                                                           
            ### [HIGH] BROKEN_CASCADE_DELETE                                      
            File: models.py:65-70 + database.py:36-53                             
            Description: `deletar_produto` não remove `itens_pedido` que        
            referenciam o produto; schema sem FK e sem `ON DELETE CASCADE`.       
            Impact: Itens órfãos; relatórios inconsistentes; `get_pedidos_usuario`
            retorna "Desconhecido".                                              
            Recommendation: FK com `ON DELETE CASCADE` ou exclusão em transação.
                                                                           
            ### [MEDIUM] N_PLUS_ONE_QUERY                                         
            File: models.py:171-201,203-233                                       
            Description: `get_pedidos_usuario`/`get_todos_pedidos`: 1 query       
            pedidos + N para itens + N*M para nome do produto.                  
            Impact: Latência cresce linearmente; degrada em produção.             
            Recommendation: Single query com JOIN. Playbook §9.                   
                                                                           
            ### [MEDIUM] MISSING_CASCADE_OR_TRANSACTION                           
            File: models.py:133-169                                               
            Description: `criar_pedido` faz 3 INSERTs/UPDATEs em diferentes
            tabelas sem `BEGIN`/`COMMIT` explícito.                               
            Impact: Estado parcial em caso de falha — pedido sem itens, estoque 
            dessincronizado.                                                      
            Recommendation: Envolver em transação; `UPDATE ... WHERE estoque >= ?`
            para race-free. Playbook §12.                                        
                                                                           
            ### [MEDIUM] DUPLICATE_VALIDATION_LOGIC
            File: controllers.py:24-62,64-96                                      
            Description: `criar_produto` e `atualizar_produto` repetem mesmo bloco
            — `atualizar` NÃO valida `len(nome)` nem categoria.                  
            Impact: Drift assimétrico; bug latente.
            Recommendation: Schema (pydantic/marshmallow) ou função               
            `validate_produto_payload`.                                         
                                                                           
            ### [MEDIUM] BARE_EXCEPT_OR_SWALLOWED_ERROR                           
            File: controllers.py (todos os handlers, ex: 10-12,60-62,95-96,...)
            Description: Padrão `except Exception as e: return jsonify({"erro":   
            str(e)}), 500` em todos os handlers.                                  
            Impact: Bugs silenciosos; mensagens vazam detalhes internos;          
            impossível distinguir 4xx/5xx.                                        
            Recommendation: Centralizar em `middlewares/error_handler.py` com   
            exceptions custom. Playbook §7.                                       
                                                                           
            ### [MEDIUM] UNVALIDATED_INPUT_TYPE                                   
            File: controllers.py:39-46,82-90,118-121,195-201,239-243              
            Description: `preco`/`estoque`/`usuario_id` lidos do JSON e comparados
            sem coerção; querystring `preco_min`/`preco_max` convertida sem      
            try/except.                                                         
            Impact: Crash 500 com payload malformado; comparação string vs int    
            silenciosamente errada.                                             
            Recommendation: Schema validation no edge.                            
                                                                           
            ### [LOW] MAGIC_NUMBER                                                
            File: controllers.py:47-50,87-90 + models.py:257-262                  
            Description: `2`, `200` para limites de nome; tiers de desconto       
            `10000/5000/1000` com `0.1/0.05/0.02`.                 
            Recommendation: Constantes nomeadas em `config/`.                     
                                                                           
            ### [LOW] DEAD_CODE_OR_UNUSED_IMPORT                   
            File: models.py:2                                                     
            Description: `import sqlite3` em models.py sem uso.                   
            Recommendation: Remover.   
                                                                           
            ### [LOW] PRINT_OR_CONSOLE_LOG                                      
            File: controllers.py (8,11,57,61,106,161,179,182,208-210,219,248,250) 
            + app.py:56,83-86                                                     
            Description: `print(...)` substituindo logging; "ENVIANDO
            EMAIL/SMS/PUSH" simulando notificações.                               
            Recommendation: `logging` configurado; notificações em                
            `services/notification_service.py`.    
                                                                           
            ### [LOW] INADEQUATE_HTTP_STATUS                                    
            File: controllers.py (handlers de exception, ex: 11-12,60-62)         
            ### [LOW] PRINT_OR_CONSOLE_LOG

            ### [LOW] PRINT_OR_CONSOLE_LOG
            File: controllers.py (8,11,57,61,106,161,179,182,208-210,219,248,250) + app.py:56,83-86
            Description: `print(...)` substituindo logging; "ENVIANDO EMAIL/SMS/PUSH" simulando notificações.
            Description: `print(...)` substituindo logging; "ENVIANDO EMAIL/SMS/PUSH" simulando notificações.
            Recommendation: `logging` configurado; notificações em `services/notification_service.py`.
            Recommendation: `logging` configurado; notificações em `services/notification_service.py`.

            ### [LOW] INADEQUATE_HTTP_STATUS

            ### [LOW] INADEQUATE_HTTP_STATUS
            File: controllers.py (handlers de exception, ex: 11-12,60-62)
            Description: Qualquer falha vira 500, inclusive ValidationError (deveria ser 400).
            Description: `import sqlite3` em models.py sem uso.
            Recommendation: Remover.

            ### [LOW] PRINT_OR_CONSOLE_LOG
            File: controllers.py (8,11,57,61,106,161,179,182,208-210,219,248,250) + app.py:56,83-86
            Description: `print(...)` substituindo logging; "ENVIANDO EMAIL/SMS/PUSH" simulando notificações.
            Recommendation: `logging` configurado; notificações em `services/notification_service.py`.

            ### [LOW] INADEQUATE_HTTP_STATUS
            File: controllers.py (handlers de exception, ex: 11-12,60-62)
            Description: Qualquer falha vira 500, inclusive ValidationError (deveria ser 400).
            Recommendation: Mapear exceptions para status corretos via middleware §7.

            ================================
            Total: 20 findings
            ================================

            Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]


            ================================                                              
            PHASE 3: REFACTORING COMPLETE                                                                                                                                                                                      
            ================================
            ## New Project Structure                                                                                                                                                                                           
            code-smells-project/                                                                                                                                                                                               
            ├── app.py                      # entrypoint (thin shim → src.app:create_app)                                                                                                                                      
            ├── requirements.txt            # + python-dotenv, + bcrypt                                                                                                                                                        
            ├── .env                        # gitignored (SECRET_KEY, DEBUG, etc.)                                                                                                                                             
            ├── .env.example                # template                                                                                                                                                                         
            ├── README.md                                                                                                                                                                                                      
            └── src/                                                                                                                                                                                                           
                  ├── app.py                  # composition root: create_app()                                                                                                                                                   
                  ├── config/
                  │   ├── settings.py         # env-driven Settings (SECRET_KEY, CORS_ORIGINS, ...)
                  │   ├── constants.py        # PRODUTO_NOME_*, CATEGORIAS_VALIDAS, DESCONTO_TIERS
                  │   └── database.py         # flask.g connection + schema (FK + ON DELETE CASCADE) + bcrypt-hashed seed
                  ├── models/
                  │   ├── produto_model.py    # SELECT/INSERT/UPDATE/DELETE com '?' placeholders
                  │   ├── usuario_model.py    # bcrypt hash/check_password + to_public (sem password_hash)
                  │   └── pedido_model.py     # JOIN único (sem N+1) + criar_com_itens transacional
                  ├── views/
                  │   ├── index_routes.py     /
                  │   ├── health_routes.py    /health  (apenas status + version)
                  │   ├── produto_routes.py   /produtos/* (GET/POST/PUT/DELETE/busca)                                                                                                                                            
                  │   ├── usuario_routes.py   /usuarios/*                                                                                                                                                                        
                  │   ├── auth_routes.py      /login                                                                                                                                                                             
                  │   ├── pedido_routes.py    /pedidos/*                                                                                                                                                                         
                  │   ├── relatorio_routes.py /relatorios/vendas     
                  │   └── admin_routes.py     /admin/* gated por X-Admin-Token (503 se não configurado)                                                                                                                          
                  ├── controllers/                                                                                                                                                                                               
                  │   ├── produto_controller.py  # validação compartilhada criar/atualizar                                                                                                                                       
                  │   ├── usuario_controller.py                                                                                                                                                                                  
                  │   ├── auth_controller.py                         
                  │   └── pedido_controller.py   # normaliza tipos e propaga ValidationError                                                                                                                                     
                  ├── services/                                                                                                                                                                                                  
                  │   ├── notification_service.py # logging estruturado (substitui prints)
                  │   └── relatorio_service.py    # cálculo de desconto via tiers                                                                                                                                                
                  └── middlewares/                                                                                                                                                                                               
                     └── error_handler.py    # AppError/NotFoundError/ValidationError/UnauthorizedError + handler global                                                                                                        
                                                                                                                                                                                                                                 
            ## Validation                                                                                                                                                                                                      
               ✓ Application boots without errors (pid logado, schema + seed idempotentes)                                                                                                                                      
               ✓ All endpoints respond correctly                                                                                                                                                                                
                  Pre-refactor:  15 chamadas → 200 / 200 / 200 / 200 / 200 / 200 / 200 / 200 / 401 / 200 / 201 / 200 / 200 / 201 / 201                                                                                         
                  Post-refactor: 20 chamadas → 200 / 200 / 200 / 200 / 200 / 200 / 200 / 200 / 401 / 200 / 201 / 200 / 200 / 201 / 200 / 200 / 201 / 200 / 503 / 503                                                           
                  (status codes idênticos para os 15 endpoints comuns; PUT/DELETE/PUT-status agora cobertos; /admin/* retornam 503 propositalmente porque ADMIN_TOKEN está vazio)                                              
                  Payload diffs (intencionais, são correções):                                                                                                                                                                 
                     • /usuarios e /usuarios/<id>: campo `senha` removido do envelope                                                                                                                                           
                     • /health: apenas {status, version} (removidos secret_key, debug, db_path, counts)                                                                                                                         
                     • /login: retorna {id, nome, email, tipo} (sem password_hash)                                                                                                                                              
               ✓ Zero CRITICAL/HIGH findings on re-audit                                                                                                                                                                        
                  • SQL_INJECTION_STRING_CONCAT  → 0 (todas queries com '?' placeholders)                                                                                                                                      
                  • HARDCODED_SECRET             → 0 (settings.py exige SECRET_KEY do env; falha no boot se faltar)                                                                                                            
                  • PLAINTEXT_PASSWORD           → 0 (coluna password_hash; bcrypt; seed re-hashed)                                                                                                                            
                  • ARBITRARY_SQL_ENDPOINT       → mitigado: gated + SELECT-only + read-only sqlite URI                                                                                                                        
                  • PII_LEAK_IN_RESPONSE         → 0 (allow-list em usuario_model._to_public)                                                                                                                                  
                  • GOD_FILE_OR_CLASS            → 0 (maior arquivo 125 LOC)                                                                                                                                                   
                  • BUSINESS_LOGIC_IN_VIEW       → 0 (views só roteiam)                                                                                                                                                        
                  • SECRET_LEAK_IN_RESPONSE_HEALTH → 0 (/health enxuto)                                                                                                                                                        
                  • GLOBAL_MUTABLE_STATE         → 0 (flask.g + teardown_appcontext)                                                                                                                                           
                  • BROKEN_CASCADE_DELETE        → 0 (FK + ON DELETE CASCADE no schema)                                                                                                                                        
                  • N_PLUS_ONE_QUERY             → 0 (1 JOIN para pedidos+itens+produtos)                                                                                                                                      
                  • MISSING_CASCADE_OR_TRANSACTION → 0 (criar_com_itens em transação com rollback)                                                                                                                             
                  • DUPLICATE_VALIDATION_LOGIC   → 0 (_validate_payload compartilhado)                                                                                                                                         
                  • BARE_EXCEPT_OR_SWALLOWED_ERROR → 0 (centralizado em error_handler)                                                                                                                                         
                  • UNVALIDATED_INPUT_TYPE       → 0 (coerções com tratamento)                                                                                                                                                 
                  • MAGIC_NUMBER, PRINT_OR_CONSOLE_LOG, DEAD_CODE → 0                                                                                                                                                          
            ================================                                                                                                                                                                                   
                                                                                                                                                                                                                                 
            Resumo: 4 arquivos achatados (app.py/controllers.py/models.py/database.py, ~780 LOC) → árvore MVC com 7 camadas em src/ (~908 LOC), todos os 20 fluxos HTTP testados batem com o contrato pré-refactor, e os 11    
            findings CRITICAL/HIGH originais foram zerados ou mitigados (admin/query foi gated + read-only em vez de removido para preservar o endpoint). 

         **Projeto code-smell-project - Execução**:
         ![Projeto code-smell-project  - Execução](/reports/runner-project-1.jpg)

      </details>


   2. **ecommerce-api-legacy**

      <details>
         <summary>Resultados - ecommerce-api-legacy</summary>

            ================================
            PHASE 1: PROJECT ANALYSIS
            ================================
            Language:       Node.js / JavaScript (CommonJS)
            Framework:      Express 4.18.2
            Dependencies:   express ^4.18.2, sqlite3 ^5.1.6
            Domain:         LMS API — checkout de cursos com enrollments, payments e audit logs (users, courses, enrollments,
            payments, audit_logs)
            Architecture:   monolithic-flat — God class única (AppManager) que faz schema + 3 rotas + payment + audit; pastas
            src/{config,controllers,middlewares,models,services,views}/ existem mas estão vazias (scaffolding aguardando
            refactor)
            Source files:   3 files analyzed (~180 LOC) — src/app.js, src/AppManager.js, src/utils.js
            DB tables:      users, courses, enrollments, payments, audit_logs (sqlite3 in-memory)
            Run command:    npm install && npm start  (porta 3000; sem seed externo — initDb() popula in-process no boot)
            ================================

            ================================
            PHASE 2 - ARCHITECTURE AUDIT REPORT
            ================================
            Project: ecommerce-api-legacy
            Stack:   Node.js + Express 4.18.2 + sqlite3 5.1.6 (in-memory)
            Files:   3 analyzed | ~180 lines of code

            ## Summary
            CRITICAL: 3 | HIGH: 7 | MEDIUM: 4 | LOW: 3

            ## Findings

            ### [CRITICAL] HARDCODED_SECRET
            File: src/utils.js:1-7
            Description: Objeto `config` exporta `dbPass`, `paymentGatewayKey` (formato `pk_live_*`), `smtpUser` e `dbUser`
            como literais. Já existe um `.env`, mas o código nunca o lê.
            Impact: Credenciais reais commitadas; rotação exige patch + redeploy.
            Recommendation: Mover para `.env` e ler via `process.env` em `src/config/settings.js`. Ver playbook §1.

            ### [CRITICAL] PLAINTEXT_PASSWORD
            File: src/AppManager.js:12,18
            Description: Coluna `pass TEXT` (sem `_hash`) e seed insere `'123'` em texto puro.
            Impact: Vazamento do banco = vazamento de senhas; CWE-256.
            Recommendation: Renomear para `password_hash` e gerar bcrypt no seed. Ver playbook §5.

            ### [CRITICAL] WEAK_HASH_FOR_AUTH
            File: src/utils.js:17-23
            Description: `badCrypto` faz 10000-iter de `Buffer.from(pwd).toString('base64').substring(0,2)` retornando 10
            chars. Determinístico, sem salt, espaço de saída minúsculo.
            Impact: Senhas efetivamente recuperáveis; equivale a não ter hash.
            Recommendation: `bcrypt.hash(pwd, 12)` / `bcrypt.compare`. Ver playbook §5.

            ### [HIGH] GOD_FILE_OR_CLASS
            File: src/AppManager.js:1-141
            Description: Classe única concentra schema, seed, 3 rotas, regra de pagamento, audit e cache.
            Impact: Não testável em isolamento; risco propaga entre rotas.
            Recommendation: Quebrar em models/controllers/views/services por entidade. Ver playbook §2.
            
            ### [HIGH] CALLBACK_HELL
            File: src/AppManager.js:28-78
            Description: `POST /api/checkout` aninha 5 níveis de callbacks com closure `processPaymentAndEnroll` no meio.
            Impact: Erro inconsistente; risco de resposta dupla.
            Recommendation: `util.promisify` + `async/await` no controller. Ver playbook §6.
            
            ### [HIGH] CALLBACK_HELL
            File: src/AppManager.js:80-129
            Description: `GET /api/admin/financial-report` coordena fan-out via contadores `coursesPending`/`enrPending`.
            Impact: Coordenação manual frágil — request pode pendurar ou responder 2x.
            Recommendation: `async/await` + 1 query com JOIN. Ver playbook §6 + §9.
            
            ### [HIGH] BUSINESS_LOGIC_IN_VIEW
            File: src/AppManager.js:43-64
            Description: Status do pagamento (`cc.startsWith("4")`), find-or-create user, enrollment, payment e audit — tudo no
               callback de rota.
            Impact: Regras de negócio acopladas ao Express.
            Recommendation: Extrair para `controllers/checkoutController` + `services/paymentService`. Ver playbook §3.
            
            ### [HIGH] SECRET_LEAK_IN_LOGS
            File: src/AppManager.js:45
            Description: `console.log` registra número do cartão (`cc`) e a chave de produção do gateway a cada checkout.
            Impact: Vazamento PCI + credencial em qualquer log aggregator. Violação direta de PCI-DSS.
            Recommendation: Remover o log; aplicar redaction se audit for necessário.
            
            ### [HIGH] BROKEN_CASCADE_DELETE
            File: src/AppManager.js:131-137
            Description: `DELETE /api/users/:id` apaga só user. Schema sem FK/CASCADE; mensagem de resposta admite "matrículas
            e pagamentos ficaram sujos".
            Impact: Dados órfãos; relatório financeiro retorna `student: 'Unknown'`.
            Recommendation: FK com `ON DELETE CASCADE` ou exclusão programática em transação.
            
            ### [HIGH] GLOBAL_MUTABLE_STATE
            File: src/utils.js:9-10,25
            Description: `globalCache` e `totalRevenue` mutáveis no escopo do módulo, exportados.
            Impact: Memory leak (cache sem bound), race conditions, testes acoplados.
            Recommendation: Cache via DI; remover `totalRevenue` (dead). Ver playbook §11.
            
            ### [MEDIUM] N_PLUS_ONE_QUERY
            File: src/AppManager.js:80-129
            Description: `1 + N + 2*M` queries no relatório (courses → enrollments → user + payment).
            Impact: Latência cresce linearmente; inviável em produção real.
            Recommendation: 1 query com LEFT JOIN agrupada em memória. Ver playbook §9.
            
            ### [MEDIUM] BARE_EXCEPT_OR_SWALLOWED_ERROR
            File: src/AppManager.js:38,41,51,55,84,133
            Description: `res.status(500).send("Erro DB"...)` sem logar `err`; linha 38 mascara erro de DB como 404; linha 133
            ignora `err` totalmente.
            Impact: Falhas silenciosas — impossível diagnosticar incidente.
            Recommendation: Middleware central + erros customizados. Ver playbook §7.
            
            ### [MEDIUM] MISSING_CASCADE_OR_TRANSACTION
            File: src/AppManager.js:50-62
            Description: `INSERT enrollment → payment → audit_log` em callbacks separados, sem `BEGIN`/`COMMIT`.
            Impact: Estado parcial — matrícula sem pagamento, pagamento sem audit.
            Recommendation: Envolver em transação. Ver playbook §12.
            
            ### [MEDIUM] UNVALIDATED_INPUT_TYPE
            File: src/AppManager.js:29-35
            Description: Body consumido sem validação de tipo (`cc.startsWith` crasha se `card` for número).
            Impact: 500 não-tratado em payloads malformados.
            Recommendation: Validar com `zod`/`joi` no edge.
            
            ### [LOW] DEAD_CODE_OR_UNUSED_IMPORT
            File: src/utils.js:10,25 ; src/AppManager.js:2
            Description: `totalRevenue` declarada/exportada/importada mas nunca atribuída.
            Impact: Confunde leitor; superfície morta.
            Recommendation: Remover.
            
            ### [LOW] PRINT_OR_CONSOLE_LOG
            File: src/utils.js:13 ; src/app.js:13
            Description: `console.log` em utility e boot.
            Impact: Logs não-estruturados.
            Recommendation: `pino`/`winston`.
            
            ### [LOW] INADEQUATE_HTTP_STATUS
            File: src/AppManager.js:38,48,135
            Description: 404 quando deveria ser 500; 400 para "Pagamento recusado" (deveria 402); DELETE retorna 200 mesmo em
            erro.
            Impact: Clientes não distinguem 5xx de erro de domínio.
            Recommendation: Mapear conforme RFC 9110.
            
            ================================
            Total: 17 findings
            ================================

            Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]


            ================================
            PHASE 3: REFACTORING COMPLETE
            ================================

            ## New Project Structure

            ecommerce-api-legacy/
            ├── .env                          (untouched — pre-existing, now actually consumed)
            ├── .env.example                  (NEW)
            ├── .gitignore                    (NEW — protects .env)
            ├── package.json                  (untouched)
            ├── api.http                      (untouched — same requests still work)
            └── src/
                  ├── app.js                    (rewrote: composition root, async bootstrap)
                  ├── config/
                  │   ├── settings.js           (NEW — env-backed, fail-fast on missing keys)
                  │   └── database.js           (NEW — promisified sqlite3, schema + seed, FK CASCADE)
                  ├── models/
                  │   ├── userModel.js          (NEW)
                  │   ├── courseModel.js        (NEW)
                  │   ├── enrollmentModel.js    (NEW)
                  │   ├── paymentModel.js       (NEW)
                  │   ├── auditModel.js         (NEW)
                  │   └── reportModel.js        (NEW — single-JOIN query)
                  ├── controllers/
                  │   ├── checkoutController.js (NEW — async/await, BEGIN/COMMIT/ROLLBACK)
                  │   ├── reportController.js   (NEW — pure transform of JOIN rows)
                  │   └── userController.js     (NEW — id validation, idempotent delete)
                  ├── services/
                  │   ├── passwordService.js    (NEW — crypto.scrypt + timing-safe compare)
                  │   └── paymentService.js     (NEW — gateway authorize stub)
                  ├── views/
                  │   ├── checkoutRoutes.js     (NEW — Router, only parsing+next(err))
                  │   ├── reportRoutes.js       (NEW)
                  │   └── userRoutes.js         (NEW)
                  └── middlewares/
                     └── errorHandler.js       (NEW — AppError + central handler)

               Removed: src/AppManager.js (god class)  ▶ split across 11 files
               Removed: src/utils.js (hardcoded secrets + globals + badCrypto)

            ## Endpoint diff (snapshot pre vs post)

            | Endpoint                         | Status pre→post | Body change
                              |
            |----------------------------------|-----------------|-------------------------------------------------------------
            -----------------|
            | POST   /api/checkout (4111…)     | 200 → 200  ✓   | identical: {"msg":"Sucesso","enrollment_id":2}
                              |
            | POST   /api/checkout (5111…)     | 400 → 400  ✓   | text "Pagamento recusado"  →  JSON {"error":"Pagamento
            recusado"}  *         |
            | GET    /api/admin/financial-report | 200 → 200  ✓ | identical array shape, identical numbers
                              |
            | DELETE /api/users/1              | 200 → 200  ✓   | "...mas as matrículas e pagamentos ficaram sujos"  →
            "Usuário deletado"  ** |

               *  Error responses now emit JSON via the central error middleware (consistent contract).
               ** The original confessional message stated a bug; FK ON DELETE CASCADE makes the statement false, so it was
            removed.
               No 5xx introduced. Status codes preserved on every endpoint.

            ## Validation
               ✓ Application boots without errors (LMS API running on port 3000)
               ✓ All endpoints respond correctly (status codes match snapshot; shape preserved on success paths)
               ✓ Zero CRITICAL/HIGH/MEDIUM findings on re-audit
               ✓ Application boots without errors (LMS API running on port 3000)
               ✓ All endpoints respond correctly (status codes match snapshot; shape preserved on success paths)
               ✓ Zero CRITICAL/HIGH/MEDIUM findings on re-audit
                  (Residual LOW only:
                     • PRINT_OR_CONSOLE_LOG — boot log + central error logger, both endorsed by playbook §7
                     • INADEQUATE_HTTP_STATUS — kept 400 for "Pagamento recusado" to preserve API contract;
                     migrating to 402 is a follow-up coordinated with API consumers)

            ## Anti-patterns resolved (vs. Phase 2 report)

               HARDCODED_SECRET            → config/settings.js reads .env (fail-fast on missing PAYMENT_GATEWAY_KEY)
               PLAINTEXT_PASSWORD          → column renamed password_hash; seed hashes "123" via scrypt
               WEAK_HASH_FOR_AUTH          → crypto.scrypt + 16-byte salt + timingSafeEqual; badCrypto deleted
               GOD_FILE_OR_CLASS           → AppManager split into 6 models + 3 controllers + 3 routers + 2 services
               CALLBACK_HELL (×2)          → util.promisify on sqlite3 + async/await throughout controllers
               BUSINESS_LOGIC_IN_VIEW      → views only parse req + call controller; payment/auth logic in services
               SECRET_LEAK_IN_LOGS         → log of card+gateway key removed
               BROKEN_CASCADE_DELETE       → schema declares FOREIGN KEY ... ON DELETE CASCADE + PRAGMA foreign_keys=ON
               GLOBAL_MUTABLE_STATE        → globalCache and totalRevenue removed; db handle initialized once
               N_PLUS_ONE_QUERY            → reportModel uses one LEFT JOIN; controller groups in memory
               BARE_EXCEPT_OR_SWALLOWED_ERROR → controllers throw AppError subclasses; central middleware logs+responds
               MISSING_CASCADE_OR_TRANSACTION → checkout flow wrapped in BEGIN / COMMIT / ROLLBACK
               UNVALIDATED_INPUT_TYPE      → checkoutController validates presence + card type; userController validates id
               DEAD_CODE_OR_UNUSED_IMPORT  → totalRevenue removed entirely
            ================================

            Resumo: 17 findings da Fase 2 endereçados (15 totalmente, 2 reduzidos a LOW residual aceitável), todos os 3 endpoints respondem com os status pré-existentes, e nenhuma dependência nova foi adicionada — npm
            install && npm start continua sendo o único caminho para subir o app. Snapshot pré/pós em /tmp/refactor-arch-snapshot/, relatório de auditoria em reports/audit-project-2.md.

      
         **Projeto ecommerce-api-legacy - Execução**:
         ![Projeto ecommerce-api-legacy - Execução](/reports/runner-project-2.jpg)

      </details>

   3. **task-manager-api**

      <details>
         <summary>Resultados - task-manager-api</summary>

            ================================
            PHASE 1: PROJECT ANALYSIS
            ================================
            Language:       Python 3
            Framework:      Flask 3.0.0
            Dependencies:   flask 3.0.0, flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1, requests 2.31.0, python-dotenv 1.0.0
            Domain:         Task Manager API (tasks, users, categories)
            Architecture:   partially-layered — models/, routes/, services/, utils/ existem; faltam controllers/, config/, middlewares/; src/ existe mas vazio (esqueleto MVC pronto para ser preenchido); rotas concentram
            validação + regra de negócio + N+1
            Source files:   16 .py files analyzed (~1160 LOC)
            DB tables:      tasks, users, categories
            Run command:    pip install -r requirements.txt && python seed.py && python app.py
            ================================

            ================================
            PHASE 2: ARCHITECTURE AUDIT REPORT
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
            Description: Handlers de rota concentram parsing, validação de domínio (status válido, prioridade 1-5, comprimento de título), regra de "overdue", lookup de FKs, persistência e serialização. A camada de view
            contém praticamente toda a lógica do domínio Task.
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
            Description: As mesmas validações de Task (título 3-200 chars, status em lista fixa, prioridade 1-5, parsing de due_date YYYY-MM-DD, normalização de tags) aparecem em create_task (linhas 96-145) e update_task
            (linhas 167-214); a função utils/helpers.py:57-108 (process_task_data) reimplementa as três pela terceira vez e nunca é chamada.
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
            File: models/task.py:15-16,52, models/user.py:14, models/category.py:11, routes/task_routes.py:31,72,215,285, routes/user_routes.py:172, routes/report_routes.py:35,42,45,71,133,
            services/notification_service.py:35, utils/helpers.py:38, seed.py:66,67,69,70,74
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
            Description: DELETE /categories/<id> remove a Category sem tratar tasks que referenciam category_id; a FK em models/task.py:14 é nullable mas não há ON DELETE SET NULL declarado, e o handler não atualiza/deleta
            dependências.
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
            Description: Imports não-usados: app.py importa os/sys/json (apenas datetime é referenciado); task_routes importa json, os, sys, time; user_routes importa hashlib, json; report_routes importa json; utils/helpers
               importa os, sys, math, hashlib.
            Impact: Ruído no namespace; linters ficam barulhentos; pode mascarar dependências reais.
            Recommendation: Remover imports não-utilizados (rodar pyflakes/ruff ajuda a confirmar).

            ### [LOW] DEAD_CODE_OR_UNUSED_IMPORT
            File: utils/helpers.py:25-50, 57-108
            Description: Funções declaradas e nunca chamadas: sanitize_string, generate_id, log_action, is_valid_color, parse_date, process_task_data. Constantes VALID_STATUSES, VALID_ROLES, MAX_TITLE_LENGTH etc. também
            nunca são importadas.
            Impact: Código morto aumenta superfície de manutenção e cria a ilusão de helpers reutilizáveis que na prática divergem das validações reais.
            Recommendation: Remover funções não-usadas; promover constantes para src/config/constants.py e importar nos schemas.
            
            ================================
            Total: 21 findings
            ================================

            Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
            
            ================================
            PHASE 3: REFACTORING COMPLETE
            ================================

            ## New Project Structure
            task-manager-api/
            ├── app.py                       # entrypoint shim → src.app:app
            ├── seed.py                      # uses sqlalchemy.delete + bcrypt
            ├── requirements.txt             # +bcrypt 4.1.2, +pyjwt 2.8.0
            ├── .env / .env.example
            └── src/
               ├── app.py                   # create_app(), composition root
               ├── config/{settings,database,constants}.py
               ├── models/{task,user,category}.py
               ├── schemas/task_schema.py
               ├── controllers/{task,user,category,report,auth}_controller.py
               ├── services/{auth,notification}_service.py
               ├── views/{task,user,category,report,auth}_routes.py + _helpers.py
               └── middlewares/error_handler.py

            ## Validation
               ✓ Application boots without errors
               ✓ All endpoints respond correctly (12/12 GET → 200; POST/login real JWT; bad payload → 400)
               ✓ Zero CRITICAL/HIGH findings on re-audit
            ================================

      **Projeto task-manager-api - Execução**:
      ![Projeto task-manager-api - Execução](/reports/runner-project-3.jpg)

      </details>

## Seção "Como Executar": pré-requisitos, comandos para executar a skill em cada projeto e como validar que a refatoração funcionou.
   Esta sessão demostra como utilizar a Skill utilizando o Claude Code.

   1. Verifique se o diretório `.claude/skills/refactor-arch` foi copiada para dentro do projeto para o qual irá ser executada a Skill;

   2. Entre no diretório do seu projeto
      ``` bash
         cd code-smells-project
      ```

   3. Inicialize o seu Claude Code:
      ``` bash
         claude
      ```
      
   4. No console do Claude Code digite:
      ```
         /refactor-arch 
      ```
   5. Neste momento ele inciará o processamento, onde ao final de cada fase será solicitada uma confirmação para avançar para a próxima.

   6. Validando se a implementação funcinou
      O README.md de cada um dos projetos demonstra como executar a aplicação. Verifique antes e depois da refatoração se a aplicação está funcional de acordo com as orientações fornecidas. Por exemplo:
      ```bash
      pip install -r requirements.txt
      python app.py
      ```
