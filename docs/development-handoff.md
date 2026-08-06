# Axiara — Development Handoff

Status: **v0.2** (2026-08-05) — task brief for the **external coding agent** (Codex / Claude Code). **Batch 1 completed** (storage layer, init enhancements, crawler engine — merged PR #25). **Batch 4 is the active handoff** (multi-user learning sync). Work per AGENTS.md: feature branch → PR into `dev`, commit-only (no auto-push/merge).

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

## 5. Batch Status

- **Batch 1 — DONE** (PR #25, merged): storage layer, init enhancements, crawler engine. 42 tests passing.
- **Batch 2 — ACTIVE (this handoff)**: costing engine + quotation generator (§7).
- **Batch 3 — ACTIVE (this handoff)**: LangGraph agents + REST API + scheduler (§8).
- **Batch 4 — DONE** (PR #29, merged): multi-user learning sync hub (`core/learnsync/`). 112 tests passing.

## 6. Task 4 — Multi-user learning sync (hub model) [P0]

Implement the hub model from `docs/learn-sync.md` (+ `docs/learn-sync-text.md` for the text variant; `docs/learn-sync-sql.md` for the optional SQL variant). New package: `src/axiara/core/learnsync/`. Reuse the storage layer (`core/storage/`) and its `PermissionManager`.

### 6.1 User identity & data-repo integration

- Generate a **stable `user-id`** at onboarding, persist in `local_config` (`[app] user_id`); machine code as fallback.
- Git integration for the central data repo (`store/`): list/create `user/<user-id>` branches, push uploads, fetch `refs/heads/user/*`, protected `main` (write rejected for users — reuse permission patterns).

### 6.2 Upload flow (user: "上传数据" / "重新上传" / "提交数据")

- Export incremental `learn_private` diff → `bundle.yaml` (provenance: user-id, timestamps, observation counts; customer-specific entries excluded by default).
- Path: `learn_inbox/<user-id>/<yyyymmdd>/bundle.yaml`; commit message `upload <user-id> <yyyymmdd> [re-upload]`.
- Commit + push to `user/<user-id>` — **only after user confirmation** (record-first). Re-upload = new dated dir; earlier pending dir flagged stale.
- CLI/agent-level confirmation gate (LangGraph `interrupt()` comes in Batch 3 — use a CLI confirm now).

### 6.3 Central review flow

- Ingest bundles from all `user/*` branches → compare against `learn_shared/` rules (same `rule_id` → version/trust; new keys → candidates; contradicts official baseline → reject).
- Produce proposals (`ADD` / `UPDATE` / `REJECT` + reason) → **admin confirms** → update `learn_shared/` + regenerate `stats/` + `manifest.json` → PR merge into `main` (data repo) → users pull.

### 6.4 Dynamic scale monitoring (D-SK10)

- Rolling-90-day metrics: active contributors, weekly upload volume, review backlog, branch/file sprawl, friction events.
- Four tiers 🟢/🟡/🟠/🔴 (per `learn-sync.md` §10.1); produce a **scale health report** (chat summary + `output/` file). Migration proposals surfaced; migration itself requires human confirmation.

### 6.5 Inactive-branch archiving (D-SK11)

- Feature off by default (`enable_branch_archive`); idle > 180 days (configurable) → candidate list → **admin confirms** → PR merge into `archive/` branch (`archive/<user-id>/<date>/`) → delete `user/<user-id>` branch → ledger. Reactivation recreates the branch (optional seed from archive).

### 6.6 Configuration

- Config fields: `[app] user_id`, `enable_branch_archive`, `branch_strategy` (A = per-user branches default | B = single `upload/` branch), scale thresholds. Wired into `scripts/init-data.sh` + config schema.

### 6.7 SQL variant (optional, later if team uses `sync_mode: sql`)

- Tables `learn_staging` / `learn_rules` / `learn_reviews` / `learn_audit` / `learn_sync_markers`; transactional apply, optimistic locking, DB grant tiers, trigger audit (per `docs/learn-sync-sql.md`). Only if the team runs SQL — text mode first.

### 6.8 Acceptance (text mode)

- Unit tests prove: (a) upload exports a valid `bundle.yaml` at the right path and pushes to `user/<user-id>` (against a local bare remote), (b) re-upload creates a new dated dir and flags the previous pending one, (c) review produces proposals and a rejected proposal never reaches `learn_shared/`, (d) archiving: candidate detection → confirm → archive merge → branch delete, (e) scale metrics compute and tier correctly, (f) a user write to data-repo `main` is rejected.
- `uv sync` passes; `pytest` passes (existing 42 + new).

## 7. Deliverables for this handoff (Batch 4)

- Code on a new branch `feat/core-batch-4` (from latest `dev`), committed incrementally; **CHANGELOG `[Unreleased]` entry added** (doc-sync discipline).
- `uv sync` passes; `pytest` passes; one PR into `dev` — **do not merge yourself**; the main agent reviews.

## 8. Task 5 — Costing engine + Quotation generator (Batch 2) [P0]

### 8.1 Costing engine (`src/axiara/core/costing/`)

Multi-dimensional cost model aligned with the learn rules taxonomy (`material` / `process-cost` / `cost-breakdown` / `pricing-tiers`):

- **Formula**: total cost = **material + labor + loss + processing** (component breakdown per `cost-breakdown` rules).
- **Inputs**: bill of materials / user query · official baseline `data/main/` (**read-only**) · learn rules (`cost-breakdown`, `process-cost`) · optional market reference `data/market/`.
- **Unit handling**: convert via the shared normalization dictionary (kg/ton/m…), never guess silently — unknown units raise a clear error.
- **Output**: total cost + per-component breakdown + `confidence` + source refs (main/learn/market).
- **Permissions**: read-only on all layers via the storage `PermissionManager`; no writes.
- **Acceptance (unit tests)**: (a) material + process cost composition, (b) loss rate / yield applied, (c) unit conversion, (d) missing data → explicit error or graceful degradation with flagged `confidence`.

### 8.2 Quotation generator (`src/axiara/core/quote/`)

- **Mode 3 (batch)**: Excel/BOM backfill with auto column detection (openpyxl).
- **Mode 3.2 (smart quote)**: default tier from learned `pricing-tiers` (low/mid/high) + constraint negotiation — when no constraints are given, present the three tiers (per `docs/business-modes.md`).
- **Template-adaptive (D12)**: ship the default quote template; adapt on the fly to user-provided templates.
- **Output**: quotation to `output/` (document/table) + chat summary (delivery per D-SK6 pattern).
- **Feedback loop**: an approved/corrected quotation emits a **learning event** → routes into `learn_private` (Phase 4 hub, `core/learnsync/`).
- **Acceptance (unit tests)**: (a) BOM → quotation, (b) three-tier defaults when no constraints, (c) constraint negotiation, (d) template adaptation, (e) approval event emitted for learning.

## 9. Task 6 — LangGraph + REST API + Scheduler (Batch 3) [P1]

### 9.1 LangGraph agents (`src/axiara/agents/`)

- Four mode graphs per `docs/business-modes.md`: **archive** (Mode 1: manual import + learn + crawl) · **query** (Mode 2) · **quote** (Mode 3) · **review** (Mode 4).
- **`crawl_agent`** integration: replace the CLI confirmation gate with LangGraph `interrupt()` (user-confirm before market writes) + checkpointer (resume long runs).
- **`learnsync` integration**: upload / review / archive flows as graph nodes (reuse `core/learnsync/`).
- Nodes reach DBs **only through the storage layer** (defense in depth, `business-modes.md` §3).
- **Acceptance**: graph builds; interrupt/resume tested; permission enforcement at node level.

### 9.2 REST API (`src/axiara/api/`)

- FastAPI app exposing: four modes (archive/query/quote/review) + upload + review-confirm + health.
- Storage layer injected; permission checks per endpoint; no business logic in handlers.
- **Acceptance**: API integration tests (fastapi TestClient).

### 9.3 Scheduler (`src/axiara/scheduler/`)

- APScheduler jobs: **weekly upload reminder** (manual trigger only — never auto-push) · **optional weekly crawler refresh** (D-SK2: produces a proposed diff, confirm-gated) · **monthly scale health report** (D-SK10) · **archive detection** (D-SK11, admin-confirmed).
- Jobs are registrations that call existing modules; no business logic duplicated.
- **Acceptance**: job registration/trigger tests.

## 10. Deliverables for this handoff (Batch 2 + 3)

- **Two PRs, sequential**: `feat/core-batch-2` → `dev` (Batch 2 first — Batch 3 depends on it), then `feat/core-batch-3` → `dev`. Branches from latest `dev`; commit incrementally; **CHANGELOG `[Unreleased]` entry per PR** (doc-sync discipline).
- `uv sync` passes; `pytest` passes (existing 112 + new); **do not merge yourself** — the main agent reviews each PR.
