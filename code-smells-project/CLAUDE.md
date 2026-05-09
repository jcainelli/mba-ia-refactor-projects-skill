# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Sample **Project 1** for the `refactor-arch` skill challenge (FullCycle MBA). The parent repo's `CLAUDE.md` (one directory up) describes the meta-challenge — read it for the full picture. This file covers what is specific to running the skill *inside* `code-smells-project/`.

This is a Flask 3 + SQLite e-commerce API written as a deliberate **monolith with intentional anti-patterns**: SQL via string concatenation (`models.py`), hardcoded `SECRET_KEY` and `debug=True` (`app.py`), plaintext password storage and login (`models.login_usuario`), `/admin/query` that executes arbitrary SQL from request body, `/health` that leaks the secret key, no input sanitization, no service layer, and a global mutable DB connection. These are **inputs** to the skill — do not "improve" them outside a Phase 3 (`/refactor-arch`) run.

## Run

```bash
pip install -r requirements.txt
python app.py        # http://localhost:5000
```

The SQLite file `loja.db` self-creates and seeds on first boot from `database.get_db()`. There is no separate seed command, no test suite, no linter — `requirements.txt` is just `flask` + `flask-cors`. If you need to reset state, delete `loja.db` (or `POST /admin/reset-db`) and reboot.

## Architecture

Four flat modules at the repo root, no packages, no layers:

- `app.py` — Flask app factory + URL registration (uses `add_url_rule`, not blueprints/decorators) + two inline admin routes (`/admin/reset-db`, `/admin/query`).
- `controllers.py` — One function per endpoint. Mixes input validation, business rules (e.g. discount tiers in `relatorio_vendas` indirectly via `models`), DB calls, and side-effects like `print()`-as-notification ("ENVIANDO EMAIL", "ENVIANDO SMS").
- `models.py` — Procedural functions that build SQL by `+` string concat against `request`-derived values. Returns plain dicts. No ORM. **All write paths are SQL-injectable by design.**
- `database.py` — Module-level singleton `db_connection`, `get_db()` lazy-inits schema and seeds.

### The `src/` skeleton

`src/` contains empty subdirectories: `config/`, `controllers/`, `middlewares/`, `models/`, `services/`, `views/`. This is the **target MVC layout** for Phase 3 of the refactor — it is intentionally empty in the boilerplate. Phase 3 should populate it (or its equivalent) and migrate the four root modules into the layered structure, without removing endpoints.

### Endpoints (acceptance surface for Phase 3)

Phase 3 succeeds only if **every** route below still responds after refactor:

```
GET    /                              POST   /pedidos
GET    /health                        GET    /pedidos
GET    /produtos                      GET    /pedidos/usuario/<usuario_id>
GET    /produtos/busca                PUT    /pedidos/<pedido_id>/status
GET    /produtos/<id>                 GET    /relatorios/vendas
POST   /produtos                      POST   /admin/reset-db
PUT    /produtos/<id>                 POST   /admin/query
DELETE /produtos/<id>
GET    /usuarios                      POST   /login
GET    /usuarios/<id>                 POST   /usuarios
```

The `/admin/query` and `/admin/reset-db` routes are part of the surface — Phase 2 should flag them as `CRITICAL`, but Phase 3 cannot silently delete them; either keep them gated or document the removal in the audit report.

## Invoking the skill here

The `refactor-arch` skill must live at `.claude/skills/refactor-arch/SKILL.md` inside this project (copied from the parent). From this directory:

```bash
claude "/refactor-arch"
```

Phase 2 must pause for human confirmation before Phase 3 touches any file. Phase 3 must leave `python app.py` booting cleanly and all endpoints above responding.

## Constraints when modifying

- The four root modules (`app.py`, `controllers.py`, `models.py`, `database.py`) and `loja.db` are the input fixture. Do not edit them outside a Phase 3 run.
- Do not add tests, linters, or dependencies to make refactoring "easier" — the skill is supposed to work on this stack as-is.
- The audit output for this project goes to `../reports/audit-project-1.md` (path defined by parent `CLAUDE.md`).
