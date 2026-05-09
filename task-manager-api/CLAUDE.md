# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Context: this is a refactor-arch target, not production code

This is **Project 3** of the FullCycle MBA `refactor-arch` skill challenge (parent `CLAUDE.md` one level up has the full picture). The code here is **intentionally smelly** — it is the *input* to the skill, not something to clean up by hand. Do not "fix" issues you find unless you are running Phase 3 of the skill, in which case follow `.claude/skills/refactor-arch/SKILL.md` exactly.

The starting architecture is classified as `partially-layered`: the folders `models/`, `routes/`, `services/`, `utils/` exist, but business logic still lives in routes, validation is duplicated, and several layers (controllers/, schemas/, middlewares/, config/, views/) are missing. An empty `src/` skeleton with the target MVC layout (`src/{config,controllers,middlewares,models,schemas,services,views}`) is already in place — Phase 3 fills it in.

## Run / dev commands

```bash
pip install -r requirements.txt
python seed.py    # MUST run before first boot — endpoints return [] otherwise
python app.py     # http://localhost:5000, debug mode
```

There are no tests, lints, or build steps. Validation in Phase 3 is "does it boot + do all original endpoints still respond" — `curl` against the routes listed below.

`app.py` calls `db.create_all()` on import, so importing `app` (e.g., from `seed.py`) creates the schema as a side effect. The SQLite file is `instance/tasks.db`.

## Architecture quick map

- **Entry:** `app.py` — registers three blueprints (`task_bp`, `user_bp`, `report_bp`), CORS-wraps everything, hardcodes `SECRET_KEY`.
- **DB session:** `database.py` exports a single `db = SQLAlchemy()` instance that every model and route imports.
- **Models** (`models/`): `Task`, `User`, `Category`. `User.tasks` is a backref from `Task`. Each model has its own `to_dict()`.
- **Routes** (`routes/`): blueprints contain validation, ORM queries, response shaping, and ad-hoc business rules (e.g., the "is this task overdue" calculation is repeated in `task_routes`, `user_routes`, and `report_routes`).
- **Services** (`services/`): only `NotificationService` exists; it is not wired into any route.
- **Utils** (`utils/helpers.py`): mixed bag — date formatting, email regex, `process_task_data` (which duplicates validation from `task_routes`).

### Endpoints (the contract Phase 3 must preserve)

```
GET    /                          GET    /health
GET    /tasks                     POST   /tasks
GET    /tasks/<id>                PUT    /tasks/<id>      DELETE /tasks/<id>
GET    /tasks/search              GET    /tasks/stats
GET    /users                     POST   /users
GET    /users/<id>                PUT    /users/<id>      DELETE /users/<id>
GET    /users/<id>/tasks          POST   /login
GET    /reports/summary           GET    /reports/user/<id>
GET    /categories                POST   /categories
PUT    /categories/<id>           DELETE /categories/<id>
```

## Intentional anti-patterns — do not silently fix

These are the audit findings the skill is supposed to surface. Listing them here so they don't get "helpfully" repaired in unrelated edits:

- **Secrets in code:** `app.py:13` (`SECRET_KEY`), `services/notification_service.py:8-10` (SMTP creds).
- **Weak crypto:** `models/user.py:29,32` use MD5 for passwords.
- **Sensitive field leak:** `User.to_dict()` (`models/user.py:21`) returns `password`.
- **Fake auth:** `routes/user_routes.py:210` returns `'fake-jwt-token-' + str(user.id)`.
- **Duplicated overdue logic:** `task_routes.py:30-39, 71-80, 282-287`, `user_routes.py:171-180`, `report_routes.py:32-43,131-135` — all hand-roll the same `due_date < now and status not in ('done','cancelled')` check instead of using `Task.is_overdue()`.
- **N+1 in `GET /tasks`:** `task_routes.py:42-57` loads `User` and `Category` per task in a loop.
- **Bare `except:`:** scattered (`task_routes.py:62, 137, 204, 236`, `report_routes.py:186, 207, 222`, `utils/helpers.py:46,49`).
- **Validation duplicated** between `routes/task_routes.py` and `utils/helpers.py:process_task_data`.
- **Schema mutation on import:** `app.py:30-31` runs `db.create_all()` at import time.
- **CORS open to `*`** by default, debug mode on.

## What lives where you might not expect

- The skill itself is checked in at `.claude/skills/refactor-arch/` (SKILL.md + 5 reference files in `references/`). Treat the skill as **source of truth for refactor behavior** — do not edit it from inside a Phase 3 run on this project.
- `.env` is committed because it is part of the boilerplate (rotate values are placeholders). The app does not currently read it — `app.py` hardcodes config. Wiring `.env` is part of the Phase 3 refactor.
- `instance/tasks.db` is gitignored-by-Flask-convention but not by `.gitignore` here; if it shows up dirty after a run, `rm` it and re-seed.

## Refactor invocation

From this directory:

```bash
claude "/refactor-arch"
```

Phase 2 *will* halt and ask for confirmation before touching files — that pause is part of the contract, not a bug.
