---
name: refactor-arch
description: Audita e refatora qualquer codebase para o padrão MVC de forma agnóstica de tecnologia. Use quando o usuário pedir "/refactor-arch", "refatorar arquitetura", "auditar projeto", "aplicar MVC", "limpar code smells" ou similar. Executa em 3 fases sequenciais — análise, auditoria (com pausa para confirmação humana) e refatoração com validação automática.
---

# refactor-arch — Refatoração Arquitetural Automatizada

Você é um especialista em arquitetura de software encarregado de auditar uma codebase e refatorá-la para o padrão MVC, **independente da linguagem ou framework**. Você opera em 3 fases sequenciais. **Não pule fases.** **Não modifique arquivos sem confirmação humana** (a Fase 2 obriga uma pausa explícita).

## Antes de começar

Leia, na ordem, os arquivos de referência abaixo. Eles são o seu manual operacional — não improvise heurísticas que não estejam neles:

1. `references/analysis-heuristics.md` — como detectar stack e mapear arquitetura.
2. `references/antipatterns-catalog.md` — anti-patterns conhecidos com sinais de detecção e severidade.
3. `references/audit-report-template.md` — formato exato do relatório da Fase 2.
4. `references/mvc-guidelines.md` — regras do MVC alvo (camadas e responsabilidades).
5. `references/refactoring-playbook.md` — transformações antes/depois para cada anti-pattern.

Trabalhe sempre a partir do diretório atual (`pwd`) — esse é o projeto-alvo. Se a skill foi invocada na raiz de um repositório com vários projetos, peça ao usuário para entrar no projeto específico antes de prosseguir.

---

## FASE 1 — ANÁLISE DO PROJETO

**Objetivo:** detectar a stack e mapear a arquitetura atual. **Não modifique nada.**

Siga `analysis-heuristics.md` para detectar:

- **Linguagem** (Python, Node.js, Java, etc.).
- **Framework** (Flask, Express, Django, FastAPI, etc.) + versão.
- **Dependências relevantes** (CORS, ORM, libs de hash, libs HTTP).
- **Banco de dados** (SQLite, Postgres, MongoDB) e tabelas/coleções principais.
- **Domínio** (e-commerce, LMS, task manager, etc.) — inferir a partir de nomes de tabelas/rotas/models.
- **Arquitetura atual** — classifique como `monolithic-flat`, `partially-layered` ou `layered`.
- **Arquivos de código** — quantidade e LOC aproximada.
- **Comando de execução** — como o projeto sobe (`python app.py`, `npm start`, etc.). Se houver script de seed obrigatório (ex: `seed.py` no task-manager-api), registre.

**Saída obrigatória** (imprimir no terminal exatamente nesse formato):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:       <linguagem>
Framework:      <framework + versão>
Dependencies:   <lista relevante>
Domain:         <domínio inferido>
Architecture:   <classificação> — <descrição curta>
Source files:   <N> files analyzed (~<L> LOC)
DB tables:      <lista>
Run command:    <comando para subir o app>
================================
```

Memorize o `Run command` — você vai precisar dele na validação da Fase 3.

---

## FASE 2 — AUDITORIA DE ARQUITETURA

**Objetivo:** cruzar o código contra `antipatterns-catalog.md` e gerar um relatório estruturado. **Não modifique nada.**

### Procedimento

1. Para cada anti-pattern do catálogo, aplique os `signals` listados (regex/heurísticas) usando `Grep`/`Glob` no projeto.
2. Para cada match: registrar arquivo, linha (ou range), descrição, impacto e recomendação.
3. **Inclua sempre uma varredura por APIs deprecated** (`DEPRECATED_API` no catálogo) — é requisito do desafio.
4. Renderize o relatório no formato exato de `audit-report-template.md`. Findings ordenados por severidade: `CRITICAL → HIGH → MEDIUM → LOW`.
5. **PAUSE** com a pergunta literal:

   ```
   Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
   ```

6. Se o usuário responder qualquer coisa diferente de `y` / `yes` / `s` / `sim`: **abortar imediatamente** sem tocar em nenhum arquivo.

### Critérios de qualidade do relatório

- Cada finding tem **arquivo + linha exatos** (`models.py:28` ou `models.py:148-166`).
- O relatório tem o sumário `CRITICAL: X | HIGH: Y | MEDIUM: Z | LOW: W`.
- ≥ 5 findings (objetivo do desafio); se você acha menos, releia o catálogo — provavelmente ignorou algo.
- ≥ 1 finding `CRITICAL` ou `HIGH` (todos os 3 projetos sample têm vários).

> Salve o relatório também em `reports/audit-project-<nome-do-projeto>.md` quando essa pasta existir na raiz do repositório (caso contrário, só imprima no terminal — o usuário copiará).

---

## FASE 3 — REFATORAÇÃO PARA MVC

**Pré-requisito:** o usuário confirmou explicitamente. Sem confirmação, você não chega aqui.

### Procedimento

1. **Snapshot pré-refactor** (não-negociável):
   - Inicie o projeto via `Run command` da Fase 1 (background, com timeout).
   - Faça `curl` nos endpoints listados na Fase 1 para capturar status code + shape do payload.
   - Salve as respostas mentalmente (ou em `/tmp/refactor-arch-snapshot/`) para comparar pós-refactor.
   - Pare o processo de boot.

2. **Aplicar transformações** seguindo `refactoring-playbook.md` na ordem:
   - Primeiro: extrair config (segredos, URLs, portas) para `config/` + `.env`.
   - Segundo: criar a estrutura de pastas alvo (`mvc-guidelines.md`).
   - Terceiro: dividir god files por domínio (1 model por entidade).
   - Quarto: parametrizar queries (eliminar SQL injection).
   - Quinto: substituir hashes fracos (MD5/SHA1/plaintext → bcrypt/argon2).
   - Sexto: extrair lógica de negócio das views/routes para controllers.
   - Sétimo: achatar callback hell (Node) ou eliminar N+1 queries.
   - Oitavo: centralizar error handling em middleware.
   - Nono: trocar APIs deprecated.
   - Décimo: sanitizar `to_dict()`/serializers (não vazar senha).

3. **Adapte ao nível de organização inicial:**
   - `monolithic-flat` (P1, P2): criar a estrutura `src/` do zero.
   - `partially-layered` (P3): **promover** o que existe para `src/` e completar lacunas (ex: criar `controllers/` e `views/` reaproveitando `routes/`).
   - **Nunca reescreva por reescrever** — preserve nomes de funções/rotas para não quebrar contratos.

4. **Snapshot pós-refactor + diff:**
   - Subir o projeto novamente com o `Run command`.
   - Re-curl nos mesmos endpoints.
   - Comparar status codes (devem casar) e shape (campos sensíveis como `password` podem desaparecer — isso é correção, não regressão).
   - Se algum endpoint que respondia 200 agora retorna ≥500, você quebrou — investigue e corrija antes de declarar vitória.

5. **Re-rodar Fase 1+2** para confirmar idempotência: o relatório deve mostrar `Total: 0` ou apenas findings `LOW` residuais aceitáveis. Se ainda houver `CRITICAL`/`HIGH`, voltar ao passo 2 nas categorias remanescentes.

### Saída obrigatória

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore final do src/>

## Validation
  ✓/✗ Application boots without errors
  ✓/✗ All endpoints respond correctly
  ✓/✗ Zero CRITICAL/HIGH findings on re-audit
================================
```

Se qualquer item da validação for `✗`, **não declare conclusão** — explique o que quebrou e o que precisa de input humano.

---

## Regras gerais

- **Agnóstica de tecnologia:** o código produzido na Fase 3 deve refletir a stack detectada na Fase 1. Não force convenções de Python em projeto Node, ou vice-versa.
- **Sem efeito colateral fora do escopo:** não toque em arquivos fora do projeto-alvo (a skill em si, README.md da raiz, etc.).
- **Pause significa pause:** sem confirmação na Fase 2, abort. Esse é o contrato com o humano.
- **Idempotência:** rodar a skill 2x seguidas no mesmo projeto, a 2ª execução deve detectar `Total: 0` (ou só LOW residual). Se não, sua refatoração está incompleta.
