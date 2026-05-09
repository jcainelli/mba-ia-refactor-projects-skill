# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Context

This project is **one of three intentionally-broken sample apps** consumed by the `refactor-arch` skill defined in the parent repo. The parent `CLAUDE.md` (one directory up) is the primary source of truth for the overall challenge — read it first. The anti-patterns in this codebase (hardcoded secrets, SQL through a god class, callback hell, weak crypto, orphaned-row deletes) are **deliberate inputs** to the skill, not bugs to fix manually. Only modify them as part of an actual Phase 3 refactor run, or when explicitly asked.

## Run

```bash
npm install
npm start            # node src/app.js — listens on PORT (default 3000)
```

There is no test, lint, or build script. SQLite runs in-memory and re-seeds on every boot via `AppManager.initDb()`, so state never persists across restarts. Sample requests for all three endpoints live in `api.http`.

A `.env` file exists with `PORT`, `PAYMENT_GATEWAY_KEY`, `SMTP_USER`, etc., **but the code does not read it** — `src/utils.js` exports a hardcoded `config` object that the rest of the app uses. This mismatch is one of the intended findings.

## Architecture (current, pre-refactor)

The app is a single god class with three Express routes wired by deep callback chains:

- `src/app.js` — 14-line entry: builds Express, instantiates `AppManager`, calls `initDb()` then `setupRoutes(app)`, then `listen()`. Do not move boot logic out of here without also refactoring `AppManager`.
- `src/AppManager.js` — owns the `sqlite3` connection, schema + seeds, **and** all route handlers. Routes:
  - `POST /api/checkout` — find-or-create user → fake-charge card (status decided by `card.startsWith("4")`) → insert enrollment → insert payment → audit log → cache. Five nested callbacks deep.
  - `GET /api/admin/financial-report` — N+1+1 fan-out across courses/enrollments/users/payments using counter variables (`coursesPending`/`enrPending`) instead of `Promise.all`.
  - `DELETE /api/users/:id` — deletes user only; leaves orphaned enrollments/payments (response message admits this).
- `src/utils.js` — hardcoded `config` (DB user/pass, payment gateway key, SMTP user), a `globalCache` mutable singleton, `logAndCache`, and `badCrypto` (10k-iter base64-substring loop — not a real hash).
- `src/{config,controllers,middlewares,models,services,views}/` — **empty scaffolding directories** pre-created as the target layout for the Phase 3 refactor. Their existence does not mean the project is layered.

### Endpoints that must keep working after any refactor

Per the parent acceptance criteria, these three must still respond after Phase 3:

- `POST /api/checkout`
- `GET /api/admin/financial-report`
- `DELETE /api/users/:id`

Validate with the requests in `api.http` before declaring a refactor done. Booting alone is not sufficient — the skill's success bar is "every original endpoint still responds."

## Skill location

`.claude/skills/refactor-arch/` is the per-project copy of the skill (currently `references/` only — no `SKILL.md` yet at time of writing). The canonical skill source lives in the parent repo; this directory is meant to be a copy, per the parent `CLAUDE.md`.
