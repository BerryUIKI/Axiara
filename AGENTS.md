# AGENTS.md — Axiara Operating Manual

You are operating in **Axiara**, a multi-agent valuation workspace: a costing engine + real-time price-fetch agent + scheduler + quotation generator, exposed via REST API.

- **First use?** You drive the onboarding: ask the user (in their language) language → storage & sync → data source per `docs/init.md`, then run `bash scripts/init-data.sh --language … --sync-mode … --backend … --data-source … [--repo-url …] [--db-dsn …]`. Docs stay English — you translate to the user.
- **Stack**: Python 3.12 · FastAPI · LangGraph · APScheduler · uv. Storage & sync (D20): personal → SQLite; team → CSV files + git sync (`store/`) with an auto local SQLite cache, or SQL server (MySQL / MariaDB / PostgreSQL).
- **Docs language**: English (D9).

## Data layout (short)

- `data/` — business layers (app-managed): `main/` official baseline (**human-only**) · `learn/` · `market/` · `uploads/`
- `.data/` — runtime (gitignored): `store/` (git-synced) · `cache/` (wipeable) · `ledger/` · `db_dump/` · `local_config/` (private). Contract: `.data.template/README.md`

## Hard rules (do / don't)

| Do | Don't |
| --- | --- |
| Read `data/main/` as the authoritative baseline | Never write or overwrite `data/main/` — human-only |
| Ensure `.data/` is initialized (ask the user per `docs/init.md`, then run `scripts/init-data.sh` with their answers) before any business operation | Never start quoting / querying before initialization is complete |
| Detect official-baseline changes (checksum manifest + git status); recover from git/snapshots; audit in `ledger/` | Never silently continue after an unexpected baseline change — report the diff and confirm with the user |
| Write to `data/learn/` / `data/market/` per the permission model | Never hand-edit `store/` — it is git-managed |
| Wipe `cache/` freely | Never delete `local_config/` or commit its contents |
| Push via feature branch + PR into `dev` | Never push directly to `main` / `dev` |
| Ask before quoting: default + project constraints | Never quote with fabricated numbers |
| **Update ALL docs (README.md + README.zh-CN.md + CHANGELOG + affected docs) before push** | Never push without syncing documentation — doc-sync discipline (see `.workbuddy/doc-sync-todo.md`); every PR adds a CHANGELOG `[Unreleased]` entry. Archived locale READMEs in `docs/README/` are NOT force-synced |

## Workflow

1. Cut a feature branch from `dev` (never from `main`); open a PR into `dev` (mirror to `main` only when asked).
2. No commits / pushes / PRs for public-facing actions without explicit user confirmation.

## Useful commands

```bash
uv sync                                    # install dependencies
bash scripts/init-data.sh                  # ensure runtime data dirs (idempotent)
uv run axiara                              # interactive agent workspace
uv run uvicorn axiara.api.main:app --reload  # REST API
```

## Where to look next

- `docs/init.md` — first-time setup & troubleshooting (one-time)
- `README.md` — project overview (multi-language portal)
- `PLAN.md` — roadmap & decisions, single source of truth
- `docs/business-modes.md` — data permission model, four modes, LangGraph mapping
- `.data.template/README.md` — runtime data directory contract
