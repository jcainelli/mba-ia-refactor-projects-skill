# Template do Relatório de Auditoria — Fase 2

Este é o **formato exato** do output da Fase 2. Não invente seções, não troque a ordem, não use markdown-fancy. O usuário compara este output contra os critérios de aceite do desafio.

---

## Estrutura

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório raiz do projeto>
Stack:   <Linguagem + Framework + versão>
Files:   <N> analyzed | ~<L> lines of code

## Summary
CRITICAL: <X> | HIGH: <Y> | MEDIUM: <Z> | LOW: <W>

## Findings

### [CRITICAL] <NOME_DO_ANTI_PATTERN>
File: <path/relativo.ext>:<linha-inicial>[-linha-final]
Description: <1-2 frases descrevendo o que está errado, em PT-BR>
Impact: <1 frase: por que é problema, em termos práticos>
Recommendation: <1 frase: como corrigir, referenciando o playbook se aplicável>

### [CRITICAL] <NOME_DO_ANTI_PATTERN>
...

### [HIGH] <NOME_DO_ANTI_PATTERN>
...

### [MEDIUM] <NOME_DO_ANTI_PATTERN>
...

### [LOW] <NOME_DO_ANTI_PATTERN>
...

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

---

## Regras de formatação

1. **Ordem dos findings:** estritamente `CRITICAL → HIGH → MEDIUM → LOW`. Dentro do mesmo nível, ordenar por arquivo + linha (alfabético/numérico).
2. **Severidade entre colchetes maiúsculos:** `[CRITICAL]`, não `[Critical]` ou `[critical]`.
3. **Nome do anti-pattern:** usar o `id` do `antipatterns-catalog.md` em UPPER_SNAKE_CASE (ex: `SQL_INJECTION_STRING_CONCAT`).
4. **Path do arquivo:** relativo à raiz do projeto auditado, sem prefixo `./` (ex: `models.py:28`, `src/AppManager.js:80-129`).
5. **Linha exata:** sempre obrigatória. Se o anti-pattern abrange várias linhas, usar range com hífen.
6. **Sem campos opcionais:** todos os 4 campos (`File`, `Description`, `Impact`, `Recommendation`) são obrigatórios para cada finding.
7. **Idioma:** PT-BR para `Description`, `Impact`, `Recommendation`. `id` e cabeçalhos podem ficar em inglês (mantém consistência com o catálogo).
8. **Total final:** soma dos findings, sem incluir summary nem cabeçalhos.

---

## Exemplo (extraído do README do desafio, levemente adaptado)

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] SQL_INJECTION_STRING_CONCAT
File: models.py:28
Description: Query SQL construída via concatenação de string com input do usuário, em get_produto_por_id.
Impact: Permite injeção arbitrária de SQL — vetor direto de extração ou modificação do banco.
Recommendation: Substituir por placeholder parametrizado (`?` no sqlite3). Ver playbook §4.

### [CRITICAL] HARDCODED_SECRET
File: app.py:7
Description: SECRET_KEY do Flask hardcoded no código-fonte.
Impact: Segredo commitado no repo; rotação requer mudar código + redeploy.
Recommendation: Mover para .env e ler via os.environ. Ver playbook §1.

### [HIGH] GOD_FILE_OR_CLASS
File: models.py:1-350
Description: Arquivo único contém lógica de 4 domínios (produtos, usuários, pedidos, relatórios).
Impact: Impossível testar em isolamento; mudanças propagam.
Recommendation: Separar em models/produto_model.py, models/usuario_model.py, etc. Ver playbook §2.

[... outros findings ...]

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

---

## Após a renderização

1. **Imprimir no terminal** o relatório completo conforme o template.
2. **Persistir** em `reports/audit-project-<nome-do-projeto>.md` se a pasta `reports/` existir na raiz do repositório (sobe de diretório até encontrar `.git`).
3. **Aguardar resposta** do usuário literal: `y`, `yes`, `s`, `sim` → prosseguir para Fase 3. Qualquer outra resposta → abortar.

Sob nenhuma circunstância modifique arquivos antes da confirmação. Esse é o contrato com o humano e o critério explícito do desafio.
