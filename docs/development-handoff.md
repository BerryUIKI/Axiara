# Axiara — Development Handoff (Batch 1)

Status: **v0.1** (2026-08-05) — task brief for the **external coding agent** (Codex / Claude Code). Branch: `feat/core-batch-1` (based on `dev`). Work per AGENTS.md: feature branch → PR into `dev`, commit-only (no auto-push/merge).

## 0. Before you start

- Read: `AGENTS.md` (hard rules), `PLAN.md` (roadmap), `docs/business-modes.md` (data layers & permissions), `docs/init.md` (data guide), `docs/skill-requirements.md` §2 (implementer split), `docs/workspace-config.md`, `docs/crawler-spec.md`, `docs/data-sources.md`, `docs/learn-sync.md`.
- Stack: **Python 3.12**, **uv** (never pip install globally), package root `src/axiara/`.
- Existing skill assets to reuse: `skills/price-crawler/config/*.yaml` (settings/adapters/sources/normalization), `skills/price-crawler/scripts/check_robots.py`, `skills/*/references/*.md`, `skills/csv-data-import/scripts/validate_csv.py`.

## 1. Hard rules (never violated)

| Rule | Where |
| --- | --- |
| **Never write `data/main/`** — official baseline is human-edit only; storage layer must reject agent writes there | `docs/business-modes.md` §1 |
| **Robots protocol is mandatory** for every crawl; `enabled: false` sources are refused | `docs/crawler-spec.md` §3, `docs/data-sources.md` |
| Crawled/learned data lands in `data/market/` / `data/learn/` **only after user confirmation** | `docs/business-modes.md` Mode 1.2 |
| `store/` is git-managed — never hand-edit | `AGENTS.md` |
| No auto-push, no direct push to `dev`/`main`, PR only | `AGENTS.md` |
| No credentials / tokens in code or configs | — |

## 2. Task 1 — Storage layer (`src/axiara/core/storage/`) [P0]

Build the file-first storage layer with permission enforcement (defense in depth, `business-modes.md` §3).

- **Data access**: CSV / JSON / YAML readers-writers over the business dirs: `data/main/` (read-only for agents), `data/learn/`, `data/market/`, `data/uploads/`.
- **Runtime dirs**: manage `.data/store/` (git-synced clone), `.data/cache/` (wipeable), `.data/ledger/`, `.data/db_dump/`, `.data/local_config/` (per `.data.template/README.md`).
- **SQLite local cache** (team CSV mode): auto-maintained in `.data/cache/`, rebuildable from CSV, never synced.
- **Write-permission enforcement**: a storage interface that rejects forbidden writes (e.g. crawler/learn write to `main`); nodes reach DBs only through it.
- **Anti-tampering hooks**: SHA-256 manifest read/compare support (`db_dump/`), ledger append API.
- **Acceptance**: unit tests prove (a) agent write to `data/main/` rejected, (b) CSV import/export idempotent, (c) SQLite cache rebuilds from CSV, (d) manifest detect/compare works.

## 3. Task 2 — init enhancements (create/join + config schema) [P0]

Implement `docs/workspace-config.md` decisions in `scripts/init-data.sh` (and/or the future `axiara init` CLI):

- New `[app]` fields: `currency`, `timezone`, `date_format`, `quote_currency`, `quote_decimals`, `industry`; new `[workspace]` section: `template_id`, `template_version`.
- **Create path**: language→currency inference table (zh-CN→CNY, en→USD, ja→JPY, ...); writes config; **automatically exports** `workspace.config.yaml` (OQ-C3 resolved: automatic).
- **Join path**: read `store/workspace.config.yaml` (or `--config-file`) → apply team values → ask only local-only items.
- Keep: no-flags runs never touch existing config; re-run backs up `config.bak`; TTY/non-interactive behavior.
- **Acceptance**: create produces a valid template; join applies it; existing configs survive no-flags runs.

## 4. Task 3 — Crawler engine (`src/axiara/core/crawler/`) [P1]

Implement the 7-step pipeline from `docs/crawler-spec.md` §3, driven by the existing configs:

1. **Prepare** — load `skills/price-crawler/config/sources.yaml`; **refuse disabled sources**; robots check (reuse `check_robots.py` logic, cache in `.data/cache/robots/`).
2. **Fetch** — httpx with timeouts/retries/backoff per `settings.yaml`; honest UA.
3. **Parse** — per-source selectors from `adapters.yaml` (CSS/XPath) or named parser.
4. **Normalize** — `normalization.yaml` dictionary; unknown aliases kept raw + flagged.
5. **Dedup/denoise** — dedup key + median-range anomaly quarantine (`settings.yaml`).
6. **Confirm** — CLI/agent-level confirmation gate before any write (storage layer enforces `data/market/` write requires a confirmed batch).
7. **Store** — normalized JSON to `data/market/<source>/<yyyymmdd>-<material>.json` + raw capture; manifest + ledger.

- **Acceptance**: a dry-run against one public HTTP source (e.g. `mofcom-cif` or `indexmundi`, both `legal: public_market_data`) produces a normalized JSON batch; a `robots.txt`-disallowed path is refused; a disabled source is refused up front.
- Out of scope for Batch 1: browser-based sources (`method: browser`), weekly scheduler wiring (Batch 4).

## 5. Batch 2+ (future handoffs, reference only)

- **Batch 2**: Costing engine (`core/costing/`) — multi-dimensional cost model; Quotation generator (`core/quote/`) — default + user templates (Mode 3.2 tiers).
- **Batch 3**: LangGraph graph & nodes (`src/axiara/agents/`) incl. `crawl_agent` + `interrupt()` confirm; APScheduler jobs (`scheduler/`); FastAPI app (`api/`).
- **Batch 4**: Tests & CI hardening (`tests/`, workflows); learn sync hub (`docs/learn-sync.md`) implementation.

## 6. Deliverables for this handoff

- Code on branch `feat/core-batch-1` (from `dev`), committed incrementally.
- `uv sync` passes; `pytest` passes for new storage/crawler tests.
- One PR into `dev` when Batch 1 is complete — **do not merge yourself**; the main agent reviews.
