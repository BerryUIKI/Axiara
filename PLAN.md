# Axiara — Project Plan

Single source of truth for Axiara initialization. Update as decisions are made; check items off when executed.

## Confirmed Decisions (2026-08-04)

| # | Decision | Choice |
| --- | --- | --- |
| D1 | Positioning | Multi-agent valuation core: costing engine + price-fetch agent + scheduler + quotation generator, exposed via RESTful API |
| D2 | Frontend | `Axiara-Web` — **deferred** (separate repo, will be created later) |
| D3 | Language / Framework | Python 3.12 + FastAPI |
| D4 | Agent framework (AgentWork) | LangGraph |
| D5 | Dependency management | uv |
| D6 | Task scheduler | APScheduler |
| D7 | Storage | Pluggable backends: PostgreSQL / SQLite / MongoDB + CSV import/export (backend selectable by user) |
| D8 | Conventions | Brand-new conventions for this repo (no inheritance from other workspaces) |
| D9 | Docs language | English |
| D10 | Git remote | None yet — to be created later and linked |
| D11 | Naming | `main` (not master) for baseline dir; `output/` (not out) for deliverables; `main_db` / `market_db` naming |
| D12 | Quote template | Open-source friendly: Agent ships a default quote template; adapts to user-provided templates on the fly |
| D13 | Quote constraints | Ask before quoting: default + project constraints; none specified → low/mid/high three tiers |
| D14 | Team permissions | Default admin-only on official lib; NOT in code — deferred to SQL DB or Git repo permissions |
| D15 | Runtime data dir | `.data/` layout: `store/` (axiara-data git sync) · `cache/` (ephemeral) · `ledger/` · `db_dump/` (PG/SQLite/Mongo — renamed from mysql_dump) · `local_config/` (private, never synced). Skeleton ships in git at `.data.template/`; `.data/` itself is gitignored; created by `scripts/init-data.sh` and auto-bootstrapped at app startup |
| D16 | Agent-facing repo | The repo's meta-user is an AI agent (human users just hand the link over). Root `AGENTS.md` is the agent operating manual: bootstrap, dir conventions, hard rules (main_db write-protection, store/ git-managed, PR-only), workflow. Initialization must be zero-touch: auto-created at startup, script as fallback |
| D17 | Agent docs: lean context | `AGENTS.md` is loaded every session → it holds ONLY per-session essentials (rules, workflow, layout short). One-time setup & troubleshooting moved to `docs/init.md`, referenced from AGENTS.md / README / `.data.template/README.md`. Principle: persistent context = per-session only; one-time ops = on-demand docs |
| D18 | Interactive onboarding | `init-data.sh` doubles as a guided wizard for non-technical users: ① language (persisted to `[app] language`) ② storage backend — SQLite default, **CSV added per user request** (D7), PG/Mongo advanced ③ data source (local files / team repo / none → guided). TTY detection: interactive for humans, non-interactive for agents/CI (never overwrites existing config; interactive reruns back up to `config.bak`). Store sync failure is a warning, not fatal. Import template: `docs/templates/price-list.csv.example`. Full guide: `docs/init.md` |
| D19 | File-first storage (modifies D7/D18) | **No server infrastructure** → data = plain text files (**CSV / JSON / YAML**) synced via git into `store/`; PostgreSQL / MongoDB removed from the wizard (server DBs not needed); SQLite demoted to optional **local cache** (not synced). `db_backend` renamed **`data_format`** (`csv | json | yaml | sqlite`). Big/binary files stay out of git (store/ is for text data files only). Doc: storage model section in `docs/init.md` |
| D20 | Storage & sync decision tree (modifies D18/D19) | First question = **do you need team sync?** → No (personal): **SQLite**. Yes (team): **① text + Git** → CSV files synced via git into `store/` (no server; Agent auto-maintains a local SQLite cache in `.data/cache/` for fast queries / token savings — always on, not a user choice) **② SQL server** → MySQL / MariaDB / PostgreSQL (needs connection string). **MongoDB excluded**; data format **defaults to CSV** (Excel-editable; no user format choice; JSON/YAML reserved for Agent-generated artifacts). Config: `[app] sync_mode` (`none|git|sql`) + `[app] backend` (`sqlite|csv|mysql|mariadb|postgresql`) + `[storage] db_dsn` (SQL only). |
| D21 | Agent-driven init & data integrity | **Onboarding Q&A is done by the Agent in the user's chosen language** — docs stay English-only (single source, no i18n sync cost); the user never reads them. `init-data.sh` is fully non-interactive with CLI flags (`--language --sync-mode --backend --db-dsn --data-source --repo-url`); no-flags runs never touch existing config. **Anti-tampering**: detect via SHA-256 manifest (stored in `db_dump/`, not `cache/`) + `git status`; recover via git history / periodic `db_dump/` snapshots / SQLite cache; audit via `ledger/` + git log. Unexpected official-baseline change → **review mode** (show diff, ask user), never silently continue. |

## Open Questions (deferred)

- **store ↔ data/main relation** — decided at storage-layer implementation: recommend `data/main` reads the official-baseline files directly from `store/` (single source of truth), not an imported copy. (Deferred by user, 2026-08-05.)
- **Sync scope** — recommendation: official baseline + optional shared ledgers enter git; `learn/`/`market/` stay local-private; `cache/`/`local_config/`/`db_dump/` never in git. (Pending user confirmation.)
- **Sync triggers** — recommendation: pull on init / app startup / periodic (APScheduler); push only on explicit human action after editing. (Pending.)
- **Conflict strategy** — recommendation: git text conflicts → Agent reports to human or auto-merges per rules. (Pending.)

## Repository State

- [x] `git init` on `main` (2026-08-04)
- [x] `README.md` — project overview (+ 9 locales)
- [x] `.gitignore` — Python / uv / FastAPI defaults (.workbuddy excluded)
- [x] `LICENSE` — MIT (2026 Berry Wahlberg)
- [x] Runtime data bootstrap — `.data.template/` skeleton (README + `local_config.example` + dirs), `scripts/init-data.sh`, `.data/` gitignored (2026-08-05)
- [x] `AGENTS.md` — lean agent operating manual (2026-08-05)
- [x] `docs/init.md` — agent-driven onboarding guide + data guide + data integrity (2026-08-05)
- [x] Agent-driven init & anti-tampering design (D21) — `init-data.sh` CLI flags, docs integrity section, AGENTS.md rules (2026-08-05)
- [x] Branch protection (2026-08-05) — `dev`: PR-only (enforce_admins, no force push/delete); `main`: PR-only + 1 review + required checks (`continuous-integration`, `pr-source-guard`) — **main PRs only from `dev` or `hotfix/*`** via `.github/workflows/pr-source-guard.yml`
- [x] Initial commit `4542acb` (2026-08-04)
- [x] Git remote — linked `https://github.com/BerryUIKI/Axiara.git`, `main` pushed (2026-08-05)

## Roadmap

- [ ] **Runtime dir auto-bootstrap** — ensure `.data/` dirs exist at app startup (fold into scaffold step)
- [ ] **`axiara init` CLI** — migrate the onboarding wizard from `scripts/init-data.sh` to Python (scaffold stage); keep the same question flow & config format
- [ ] **Scaffold package** — `uv init`, `pyproject.toml`, `src/` layout, `axiara` package
- [ ] **Business modes design** — 4 modes + 3-layer data permission model (draft at `docs/business-modes.md`, open questions pending) → fold into README as English overview once settled
- [ ] **Storage layer** — file-first (CSV / JSON / YAML) + git-synced `store/`; SQLite as optional local cache; write-permission enforcement at this layer
- [ ] **Costing engine** — multi-dimensional cost model, rules, calculation pipeline
- [ ] **Price fetch agent** — LangGraph agent: crawl + normalize real-time market prices
- [ ] **Learning engine** — ingest historical quotes/invoices → clean → extract material/process/cost/pricing rules → `learn_db` (design: `docs/learning-plan.md`, phases 0–5)
- [ ] **Task scheduler** — APScheduler jobs: periodic price fetch, scheduled quotation generation
- [ ] **Quotation generator** — compose cost + price into quotations
- [ ] **REST API** — FastAPI endpoints for external clients
- [ ] **Tests & CI** — unit/integration tests, CI pipeline
- [ ] **Git remote** — create remote repo, link, push per PR-only workflow (remote not created yet)

## Execution Policy

Per workspace convention: record first, execute on request. Git commits / pushes / PRs only after explicit confirmation.
