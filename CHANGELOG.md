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
- **Multi-user learning (hub model)**: personal library (专属调教库) → weekly manual upload → central training Agent review → admin confirmation → public library; upload triggers (上传数据 / 重新上传 / 提交数据), date + user-id export (`learn_inbox/<user-id>/<yyyymmdd>/bundle.yaml`), data-repo branch rules (protected `main`, per-user `user/<user-id>` branches, `archive/` branch, branch-strategy choice A/B with default A, scale thresholds + dynamic monitoring, migration paths Git A→B→SQL, inactive-branch archiving).
- **Decision records**: D-SK1–D-SK11 (platform scope, crawler triggers, sources, init model, training report output, single-source skills, AI-friendly format, upload/branch rules, dynamic scale monitoring, inactive-branch archiving).
- **Batch 1 implementation** (PR #25): storage layer (`core/storage/` — `permissions.py` defense-in-depth write permission, `cache.py` SQLite cache, `manifest.py` SHA-256 manifest, `git_sync.py`, `file_backend.py`), crawler engine (`core/crawler/` — 7-step pipeline: prepare/fetch/parse/normalize/store with robots check + user confirmation), init script enhancement (`--default-currency`, language→currency inference, `workspace.config.yaml` export), deps (httpx/beautifulsoup4/lxml/pyyaml), tests (42 passing).

### Changed

- Initialization model: **create vs join** — everything pre-filled from inference (currency by language, timezone by OS, date/quote formats), confirm-or-edit; `workspace.config.yaml` auto-exported.
- Document discipline: **docs must be updated before push** (including README + 9 locales); changes tracked in `.workbuddy/doc-sync-todo.md`.
- Learned-data format: **AI-friendly first** — YAML preferred, JSON only for machine exchange.

## [0.1.0] - 2026-08-04

Initial scaffold (`4542acb`):

- Repository skeleton: `README.md` (+9 locales), `AGENTS.md`, `PLAN.md`, `.gitignore`, `LICENSE` (MIT), `.data.template/`, `scripts/init-data.sh`, `src/axiara/` package skeleton (`cli.py`), `docs/init.md`, `docs/business-modes.md`, branch protection (dev/main PR-only), CI workflows (`auto-release`, `pr-source-guard`), git remote linked.
