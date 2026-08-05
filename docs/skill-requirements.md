# Axiara — Skill Requirements (Development Backlog)

Status: **v0.2** (2026-08-05) — platform scope extended (WorkBuddy + Codex + Claude), crawler decisions locked (OQ-1 resolved, OQ-2/OQ-3 defined in `docs/data-sources.md`), implementer split defined. Pending user confirmation before implementation.

Workflow: **record-first**. This document is the single source of truth for what skills the Axiara workspace needs. No skill is created and no crawler code is written until the user references this document and says "execute". Git commits / pushes / PRs only after explicit confirmation (per AGENTS.md).

## 1. Skill Platforms

Each capability below is authored once and deployed to one or more of these platforms (same SKILL.md format, different install roots):

| Platform | Format | Install location | Primary owner |
| --- | --- | --- | --- |
| **WorkBuddy** | `SKILL.md` + frontmatter | `~/.workbuddy/skills/<name>/` (user-level) | WorkBuddy agent (this workspace) |
| **Codex** (OpenAI) | `SKILL.md` + frontmatter | `.codex/skills/<name>/` (repo) or `~/.codex/skills/<name>/` | External coding agent (Codex CLI) |
| **Claude** (Claude Code) | `SKILL.md` + frontmatter | `.claude/skills/<name>/` (repo) or `~/.claude/skills/<name>/` | External coding agent (Claude Code) |

Convention: skills live in the repo under `skills/<platform>/<name>/SKILL.md` (or the platform-native dot-dir when the user prefers), one source of truth, deployed to each platform root.

## 2. Implementer Split (who writes what)

| # | Work item | Implementer |
| --- | --- | --- |
| W1 | Spec & template docs (`skill-requirements.md`, `crawler-spec.md`, `data-sources.md`) | **WorkBuddy agent** (done) |
| W2 | WorkBuddy skills: SK-01/02/03 `SKILL.md` definitions + normalization dictionaries + adapter config templates | **WorkBuddy agent** |
| W3 | Codex / Claude skill definitions (same content, platform-format) | **WorkBuddy agent** writes; deployed to repo dot-dirs |
| C1 | Storage layer module (`src/axiara/core/storage/`) — file-first + git `store/` + SQLite cache + write-permission enforcement | **External coding agent** (Codex / Claude Code) |
| C2 | Crawler engine (`src/axiara/core/crawler/` or `agents/crawl_agent`) — httpx fetch/retry, robots check, adapters, normalization, dedup | **External coding agent** |
| C3 | Costing engine (`core/costing/`), quotation generator (`core/quote/`) | **External coding agent** |
| C4 | LangGraph graph & nodes (`src/axiara/agents/`), APScheduler jobs (`src/axiara/scheduler/`), FastAPI app (`src/axiara/api/`) | **External coding agent** |
| C5 | Tests & CI (`tests/`, workflows) | **External coding agent** |
| H1 | Helper scripts bundled in crawler skill (referenced by SK-03) | **External coding agent** (WorkBuddy skill references them) |

Rule of thumb: **workflows/specs/configs → WorkBuddy agent; Python code modules → external coding agent.**

## 3. Summary Table

| ID | Skill | Platform | Priority | Implementer | Status | Key contents |
| --- | --- | --- | --- | --- | --- | --- |
| SK-01 | axiara-onboarding | WorkBuddy + Codex + Claude | P0 | WorkBuddy (def), deploy 3 platforms | **Created** (2026-08-05) | Agent-driven init Q&A → `init-data.sh` flags → decision tree → anti-tampering orientation |
| SK-02 | csv-data-import | WorkBuddy + Codex + Claude | P0 | WorkBuddy (def) | **Created** (2026-08-05) | price-list.csv → `data/main/`; invoice learning → `data/learn/`; SHA-256 manifest & diff |
| SK-03 | price-crawler (commodity prices) | WorkBuddy + Codex + Claude | P1 | WorkBuddy (spec+skill def); **coding agent (engine, adapters)** | **Created** (2026-08-05); engine via coding agent | Compliance → fetch → parse → normalize → dedup → confirm → store; site adapters |
| SK-04 | storage-layer-playbook | Codex + Claude (primary) | P1 | Coding agent (impl) + WorkBuddy (playbook) | Deferred until storage layer built | file-first storage patterns, `store/` git-sync, SQLite cache, permission enforcement |
| SK-05 | finance-quotes (reference) | WorkBuddy | P2 | n/a — existing | **Covered** | `westockdata` / `a-stock-data` / `westock-tool` already installed; not needed for commodity prices |
| SK-06 | quote-export (reference) | WorkBuddy | P2 | n/a — existing | **Covered** | `tencent-docs` / local Office skills for `output/` deliverables |

## 4. Requirements Detail

### SK-01 — axiara-onboarding (P0)

- **Purpose**: every fresh clone / reinstall runs the same agent-driven bootstrap.
- **Trigger**: first use of a workspace; `.data/` wiped or corrupted; user changes language / storage-sync / data source.
- **Content**: ① Q&A in user's language (language → team sync? → backend → data source → repo URL / DSN) ② map to `scripts/init-data.sh` flags ③ post-run verification (`.data/` layout, `store/` sync, `local_config/config`, manifest) ④ anti-tampering orientation (review mode).
- **Acceptance**: a fresh clone reaches a working, verified state with no questions beyond the intended Q&A.
- **Implementer**: WorkBuddy agent writes `SKILL.md`; deployed to WorkBuddy + `.codex/skills/` + `.claude/skills/`.

### SK-02 — csv-data-import (P0)

- **Purpose**: official price lists are the highest-weight baseline; import must be reliable, versioned, tamper-evident.
- **Trigger**: *"import price-list.csv into data/main/"*; upload of historical invoices/orders for learning.
- **Content**: template validation (fields `name,spec,unit,unit_price,currency,effective_date,note`, `#` comments, ISO currency), versioned write with diff+confirm, SHA-256 manifest in `db_dump/`, ledger entry, learning path → `data/learn/` (Mode 1.2).
- **Acceptance**: idempotent import; user-reviewable manifest diff; never touches `data/main/` without confirmation.
- **Implementer**: WorkBuddy agent; storage-layer code it calls (C1) by coding agent.

### SK-03 — price-crawler, commodity prices (P1)

- **Purpose**: fetch public market prices for commodities/materials, normalize, land in `data/market/` (reference only). Design: `docs/crawler-spec.md`; sources: `docs/data-sources.md`.
- **Trigger**: *"fetch current market price for X"* / review mode needs market reference / manual crawl (on-demand, P4); optional weekly refresh (confirmed 2026-08-05).
- **Content**: compliance guardrails (robots.txt / ToS / UA / rate limit / no paywall bypass); 7-step pipeline (prepare → fetch → parse → normalize → dedup/denoise → **confirm** → store); config-driven site adapters; provenance fields; error handling; LangGraph `interrupt()` + checkpointer.
- **Acceptance**: never writes `data/main/`; every `data/market/` insert is user-confirmed, traceable, reproducible.
- **Implementer**: WorkBuddy agent = skill spec + SKILL.md + normalization dict + adapter templates (W2/W3); **external coding agent = engine + adapters + helpers (C2/H1)**.

### SK-04 — storage-layer-playbook (P1, deferred)

- **Purpose**: codify storage-layer permission patterns once built (defense in depth, business-modes §3).
- **Status**: create at storage-layer implementation time. Engine code by coding agent (C1); the playbook itself is a convention skill (WorkBuddy can author, coding agent can also).

### SK-05 / SK-06 — existing coverage (reference)

- Financial quotes (`westockdata`, `a-stock-data`, `westock-tool`, `wb-finance-skill`): installed; **out of scope** for commodity prices — SK-03 is built in-house.
- Quote/Office export (`tencent-docs` etc.): installed; use for `output/` deliverables (P3).

## 5. Decisions Log (2026-08-05)

- **D-SK1** — Platform scope: WorkBuddy + Codex + Claude; one source, deploy per platform (user request).
- **D-SK2** — Crawler trigger (OQ-1): **on-demand manual + optional weekly refresh**, refresh produces proposed diff only, never auto-insert (user confirmed).
- **D-SK3** — Target sources (OQ-2): **Agent-defined** standard template + initial recommended list in `docs/data-sources.md`; all sources must respect robots protocol; enabled only after legal check (user delegated).
- **D-SK4** — Fetch method (OQ-3): decided per source in `data-sources.md` (HTTP-first; browser only for JS-heavy B2B platforms) (user delegated).

## 6. Open Questions

- **OQ-4** — Which specific sources to enable first (from `data-sources.md` initial list) — user picks after reviewing the list.
- **OQ-5** — Skill install roots: repo dot-dirs (`.codex/skills/`, `.claude/skills/`) vs user-home roots — repo is recommended for team/CI consistency.

## 7. Status Tracking

- [x] 2026-08-05 — repo scan → v0.1 requirements + crawler spec
- [x] 2026-08-05 — v0.2: platform scope (WorkBuddy/Codex/Claude), decisions D-SK1..4, implementer split, `docs/data-sources.md`
- [x] 2026-08-05 — SK-01/02/03 created: source in `skills/<name>/SKILL.md`, deployed to `.codex/skills/`, `.claude/skills/`, and `~/.workbuddy/skills/` (WorkBuddy, local-only)
- [ ] SK-03 engine + adapters — external coding agent, after storage layer
- [ ] SK-04 storage-layer-playbook — deferred to storage-layer implementation
