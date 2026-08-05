# Changelog

All notable changes to the Axiara workspace. Format based on [Keep a Changelog](https://keepachangelog.com/).

## Structure

- **`Unreleased`** — changes merged into `dev` (development) since the last release. **This section is the `dev` change log.**
- **`[vX.Y.Z]`** — released versions from `main`. **When publishing a GitHub Release, use the corresponding `main` version entry as the release notes.**

Maintenance rule: **every PR merged into `dev` must add its entry under `Unreleased` before push** (doc-sync discipline). When `main` releases (`auto-release` workflow), the `Unreleased` content is consolidated into a dated version entry.

## [Unreleased] — dev branch

### Added

- **Skills** (`skills/`): `axiara-onboarding` (create/join dual-path init, pre-filled inference), `csv-data-import` (template validation, manifest & ledger), `price-crawler` (robots-protocol, 7-step pipeline) + infrastructure (validation/verification scripts, YAML configs: sources/adapters/normalization/settings, references, assets, LICENSE).
- **Docs**: skill-requirements (backlog, platform scope, decisions D-SK1–11, implementer split), crawler-spec (commodity price crawler), data-sources (source registry template + candidates), workspace-config (create/join + config templates + pre-filled inference), learning-plan (learn_db training plan), training-scenarios (S1–S13), learn-sync (hub model) + learn-sync-text / learn-sync-sql (implementation variants), development-handoff (Batch 1 brief).
- **Multi-user learning (hub model)**: personalized tuning library → weekly manual upload → central training Agent review → admin confirmation → public library; upload triggers ("upload my data" / "re-submit" / "submit my library"), date + user-id export (`learn_inbox/<user-id>/<yyyymmdd>/bundle.yaml`), data-repo branch rules (protected `main`, per-user `user/<user-id>` branches, `archive/` branch, branch-strategy choice A/B with default A, scale thresholds + dynamic monitoring, migration paths Git A→B→SQL, inactive-branch archiving).
- **Decision records**: D-SK1–D-SK11 (platform scope, crawler triggers, sources, init model, training report output, single-source skills, AI-friendly format, upload/branch rules, dynamic scale monitoring, inactive-branch archiving).
- **Batch 1 implementation** (PR #25): storage layer (`core/storage/` — `permissions.py` defense-in-depth write permission, `cache.py` SQLite cache, `manifest.py` SHA-256 manifest, `git_sync.py`, `file_backend.py`), crawler engine (`core/crawler/` — 7-step pipeline: prepare/fetch/parse/normalize/store with robots check + user confirmation), init script enhancement (`--default-currency`, language→currency inference, `workspace.config.yaml` export), deps (httpx/beautifulsoup4/lxml/pyyaml), tests (42 passing).
- **Batch 2 implementation** (PR #32): costing engine (`core/costing/` — `engine.py` multi-dimensional cost model with formula `total = material + labor + loss + processing`, `UnitConverter` for weight/length/area/volume conversions, read-only access via storage `PermissionManager`, graceful degradation on missing data) + quotation generator (`core/quote/` — `generator.py` Mode 3.2 smart quotation with three-tier pricing (low/mid/high), constraint negotiation (min_margin, price_cap, price_floor), template adaptation (default + user-provided), `LearningEvent` emission for approved/corrected quotes), tests (43 new: 155 total passing).
- **Batch 3 implementation** (this PR): LangGraph agents (`src/axiara/agents/` — `state.py` `AgentState` TypedDict, `nodes.py` 9 agent nodes for four modes, `graphs.py` 4 graph builders with `interrupt()` support + `MemorySaver` checkpointer), FastAPI REST API (`src/axiara/api/` — `main.py` endpoints for archive/query/quote/review + upload + review-confirm + health, Pydantic models, TestClient support), APScheduler jobs (`src/axiara/scheduler/` — `jobs.py` weekly upload reminder, optional weekly crawler refresh, monthly scale health report, archive detection), tests (42 new: 197 total passing).
- **Batch 4 implementation** (this PR): multi-user learning sync hub model (`core/learnsync/` — `user_id.py` stable user identity with machine-code fallback, `bundle.py` YAML export with provenance & validation, `upload.py` manual upload flow with user confirmation & user/<user-id> branch push, `review.py` central review (ingest → compare → propose → admin confirm → apply), `monitor.py` dynamic scale monitoring (rolling 90-day metrics, 🟢/🟡/🟠/🔴 tier classification, Git→SQL migration proposals), `archive.py` inactive-branch archiving (180-day idle detection, admin-confirmed archive merge, reactivation with seed)), init script new fields (`--user-id`, `--branch-strategy A|B`, `--enable-branch-archive`), tests (70 new: 112 total passing).
- **Batch 2/3 task briefs** (this PR): `development-handoff.md` §8 Task 5 (costing engine + quotation generator — multi-dimensional cost model, three-tier quoting, template adaptation, learning feedback loop) and §9 Task 6 (LangGraph four-mode graphs + `interrupt()` confirm, FastAPI app, APScheduler jobs).

### Changed

- Initialization model: **create vs join** — everything pre-filled from inference (currency by language, timezone by OS, date/quote formats), confirm-or-edit; `workspace.config.yaml` auto-exported.
- Document discipline: **docs must be updated before push** (including README + 9 locales); changes tracked in `.workbuddy/doc-sync-todo.md`.
- Learned-data format: **AI-friendly first** — YAML preferred, JSON only for machine exchange.
- **Doc sync (2026-08-05)**: README + 9 locales updated (Skills, multi-user hub, docs index, roadmap); AGENTS.md hard rule "docs must be updated before push"; PLAN.md D-SK1–11 reference; `.data.template/README.md` store layout; `auto-release.yml` release notes now read from CHANGELOG version entries.
- **Batch 4 doc sync (2026-08-05)**: README + 9 locales — roadmap checkbox for the multi-user learning hub ticked, "what's implemented" section now lists `core/learnsync/` and 112 tests (catch-up after PR #29).
- **Batch 3 hotfix (2026-08-05)**: utf-8 reads for crawler YAML (`pipeline.py`/`prepare.py` — fixes Windows gbk `UnicodeDecodeError` on Chinese YAML); graph entry routing via `_archive_route`/`_quote_route` on `user_input.action` (fixes `unhashable type: dict` from `dispatcher_node`), `edit_review` conditional edge `"__end__": END`; API `ainvoke` calls pass `configurable.thread_id` (checkpointer requirement); scheduler `register_jobs()` idempotent via `remove_all_jobs()` (fixes duplicate registration 44≠4); tests updated (`test_scheduler` async, `test_agents` thread_id). Full suite: 206 passing.
- **Trigger-word localization (2026-08-05)**: upload triggers localized per locale — English docs now use "upload my data" / "re-submit" / "submit my library" (DE/ES/FR/JA/KO/PT/RU locales in their own languages; zh-CN/zh-TW keep Chinese); "专属调教库" → "personalized tuning library", "唯一机器码" → "unique machine code" (README + 8 locales, `docs/learn-sync*.md`, `docs/skill-requirements.md` D-SK9). Cleanup: `output/*.json` runtime artifacts gitignored (keeps `output/.gitkeep`).

## [0.1.0] - 2026-08-04

Initial scaffold (`4542acb`):

- Repository skeleton: `README.md` (+9 locales), `AGENTS.md`, `PLAN.md`, `.gitignore`, `LICENSE` (MIT), `.data.template/`, `scripts/init-data.sh`, `src/axiara/` package skeleton (`cli.py`), `docs/init.md`, `docs/business-modes.md`, branch protection (dev/main PR-only), CI workflows (`auto-release`, `pr-source-guard`), git remote linked.
