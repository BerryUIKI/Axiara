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

## Repository State

- [x] `git init` on `main` (2026-08-04)
- [x] `README.md` — project overview
- [x] `.gitignore` — Python / uv / FastAPI defaults
- [ ] Initial commit (awaiting confirmation)

## Roadmap

- [ ] **Scaffold package** — `uv init`, `pyproject.toml`, `src/` layout, `axiara` package
- [ ] **Business modes design** — 4 modes + 3-layer data permission model (draft at `docs/business-modes.md`, open questions pending) → fold into README as English overview once settled
- [ ] **Storage layer** — storage abstraction with pluggable backends (PostgreSQL / SQLite / MongoDB) + CSV import/export; write-permission enforcement at this layer
- [ ] **Costing engine** — multi-dimensional cost model, rules, calculation pipeline
- [ ] **Price fetch agent** — LangGraph agent: crawl + normalize real-time market prices
- [ ] **Task scheduler** — APScheduler jobs: periodic price fetch, scheduled quotation generation
- [ ] **Quotation generator** — compose cost + price into quotations
- [ ] **REST API** — FastAPI endpoints for external clients
- [ ] **Tests & CI** — unit/integration tests, CI pipeline
- [ ] **Git remote** — create remote repo, link, push per PR-only workflow

## Execution Policy

Per workspace convention: record first, execute on request. Git commits / pushes / PRs only after explicit confirmation.
