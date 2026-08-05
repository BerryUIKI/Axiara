# Axiara — Multi-User Learning: SQL Server Format

Status: **v0.1** (2026-08-05) — implementation design for the **SQL-server storage mode** (`sync_mode: sql`, `backend: mysql|mariadb|postgresql`). Companion to `docs/learn-sync.md` (hub model overview) and `docs/learn-sync-text.md` (the text+git variant). Central library is a shared database; personal libraries stay local.

## 1. Model

```
user A local SQLite (private) ─┐
user B local SQLite (private) ─┼── weekly manual upload ──▶ CENTRAL DB  learn_staging (upload area)
user C local SQLite (private) ─┘         │   (INSERT / dump import)
                                         ▼
                       central training Agent reviews (SELECT staging) ──▶ admin confirms ──▶ learn_rules updated (transaction + audit)
                                                                                                   │
                                                       users pull back (read-only SELECT/merge)
```

Same hub-and-spoke logic as `docs/learn-sync.md`, implemented with **tables + transactions** instead of files.

## 2. Physical Structure

### Central database schema

| Table | Purpose | Written by |
| --- | --- | --- |
| `learn_staging` | Upload area — one row per uploaded rule proposal | Users (via upload), app layer |
| `learn_rules` | **Public rules** — the authoritative shared library | Review step only (transaction) |
| `learn_reviews` | Review decisions (per proposal: action + reviewer + reason) | Admin/reviewer |
| `learn_audit` | Append-only change log (before/after, actor, ts) | App layer (trigger or explicit) |
| `learn_sync_markers` | Per-user last-upload marker (for incremental uploads) | App layer |

Key columns:

```sql
-- learn_staging (upload area)
id BIGINT PK, contributor TEXT, uploaded_at TIMESTAMPTZ,
kind TEXT, rule_key TEXT,        -- canonical key (YAML/JSON text) + extracted query cols
value TEXT,                      -- YAML preferred (AI-readable, D-SK8); JSON allowed
trust TEXT, version INT,
status TEXT DEFAULT 'pending',          -- pending | reviewed
payload_raw TEXT,                -- original bundle row verbatim (YAML preferred; audit)

-- learn_rules (public)
rule_id TEXT PK, kind TEXT, rule_key TEXT UNIQUE, value TEXT,  -- YAML preferred
trust TEXT, contributor TEXT, version INT, updated_at TIMESTAMPTZ,
superseded_by TEXT NULL         -- tombstone (NULL = active)

-- learn_reviews
id BIGINT PK, staging_id BIGINT, action TEXT,  -- ADD | UPDATE | REJECT
reviewer TEXT, reason TEXT, decided_at TIMESTAMPTZ

-- learn_audit
id BIGINT PK, ts TIMESTAMPTZ, actor TEXT, table_name TEXT,
before TEXT, after TEXT, action TEXT    -- before/after stored as YAML/JSON text (readable audit)
```

> **Format note (D-SK8):** store rule payloads as **YAML text** — the AI reviews them directly and diffs are readable. Use dedicated columns (`rule_key`, `trust`, `version`, ...) for indexed queries; use JSONB only when the DB must query *inside* the payload (PostgreSQL) — otherwise YAML text is preferred. `learn_audit.before/after` as text keeps the audit human/AI-readable.

### Personal library (local, never synced)

- `sync_mode: sql` personal layer: **local SQLite** (`.data/learn/private.db`) or local files — user's tuned rules, customer-tier, personal habits.

## 3. Weekly Upload Protocol (SQL mode)

- **Trigger**: user says **"上传数据" / "重新上传" / "提交数据"** (or English: *"upload my data" / "re-submit" / "submit my library"*) or the weekly reminder fires — **manual, confirmed** (OQ-LS2).
- **User identity**: unique machine code / user id (`contributor`), sanitized `[a-zA-Z0-9_-]`; every staging row carries it.
- **Export**: the Agent exports the incremental diff of the personal library since the last upload marker (`learn_sync_markers`), tagged with `contributor` + date.
- **Upload**: application-layer `INSERT` into `learn_staging` (or a validated dump import). Direct writes to `learn_rules` are **rejected** for users. No git branches — identity is a column, not a branch.
- **Re-upload**: new staging rows with fresh `uploaded_at`; the earlier pending rows of that contributor are flagged stale (no silent overwrite).
- **Scoping**: customer-specific entries excluded by default (user choice).

## 4. Central Review Flow (SQL mode)

1. **Ingest** — training Agent reads new `learn_staging` rows (`status = 'pending'`), validates JSONB schema, ledger/audit entry.
2. **Compare** — against `learn_rules`:
   - same `rule_id` → version/trust comparison
   - same `rule_key` different id → new-rule candidate / conflict pair
   - contradicts official baseline → reject candidate
3. **Propose** — one `learn_reviews` row per decision: `ADD` / `UPDATE` (with before/after) / `REJECT` (with reason).
4. **Confirm** — admin accepts/rejects each proposal (review UI or CLI).
5. **Apply** — in a **single transaction**:
   - `learn_rules`: insert/update accepted rows (version bump, `updated_at`), tombstone removals
   - `learn_reviews`: mark staging rows `reviewed` + write decisions
   - `learn_audit`: append every change (before/after)
   - Rebuild derived stats (materialized view or app-level aggregates)
6. **Pull back** — users read `learn_rules` (read-only) and merge locally; personal overrides stay local.

## 5. Rule Format, Versioning & Conflicts (SQL mode)

- Versioning: optimistic locking on `learn_rules.version` — an UPDATE includes `WHERE version = <expected>`; mismatch → proposal conflicts, surfaces in review.
- Trust order: `user_rule > stats > llm` (independent of version).
- Same `rule_key`, different contributors → both staged, both surface in review as a conflict pair — never silently resolved by the DB.
- Deletes = tombstone (`superseded_by` set), never hard-delete — prevents stale syncs resurrecting removed rules.
- Stats are derived (view/rebuild), never merged by hand.
- **Concurrency**: staging and rules are separate tables → uploads never block reviews; applies are atomic transactions (no partial public updates).

## 6. Security & Privacy (SQL mode)

- **DB account tiers**: user accounts = `learn_staging` INSERT + `learn_rules` SELECT only; reviewer/admin = full review + apply. Enforced by the application layer AND database grants (defense in depth).
- Personal/customer data never enters the central DB unless the user explicitly uploads it (and can exclude customer dimensions).
- `learn_rules` contains price tiers / cost rules only — no credentials, no `local_config`, no `db_dsn`.
- `learn_audit` is append-only (trigger-enforced) — full audit trail.
- Connection string from `local_config [storage] db_dsn`; never committed.

## 7. Concurrency & Scale

- Uploads (staging INSERTs) and reviews (rule applies) are decoupled → no write contention.
- Transactions give atomic applies; optimistic locking gives safe concurrent reviews.
- Scales beyond text mode (large teams, concurrent uploads, complex queries).
- PostgreSQL recommended for JSONB; MySQL/MariaDB work with JSON column + app-side validation.

## 8. Reusable Assets

- Storage layer (`development-handoff.md` Batch 1) — SQL access primitives live there; DSN from config.
- `skills/csv-data-import/scripts/validate_csv.py` → basis for bundle/JSONB validation before staging.
- `skills/price-crawler/config/normalization.yaml` → shared alias dictionary.

## 9. Acceptance for Batch 4 (hub implementation)

- Upload flow inserts staging rows only; a direct user write to `learn_rules` is rejected (app + DB grant).
- Review flow produces decisions; applying a batch is atomic (all-or-nothing).
- Audit trail captures every apply (before/after, actor, ts).
- Pull-back merges read-only; local overrides win.

## 10. Open Questions

- **OQ-LS1** — Central library location for text mode (in `store/` vs separate repo) — this SQL design assumes the DB is the central library; no separate repo needed. Confirm.
- **OQ-LQ1** — DB choice priority: PostgreSQL (JSONB, recommended) vs MySQL/MariaDB — decide per team infrastructure; both supported in `init-data.sh`.
- **OQ-LQ2** — Audit via DB trigger vs app layer only — recommend trigger (cannot be bypassed by direct SQL).

## Mode Selection

| Dimension | Text (text+git) | SQL server |
| --- | --- | --- |
| Infrastructure | none (git only) | shared DB server + DSN |
| Concurrency | serialized by review step | concurrent, transactional |
| Scale | small teams | larger teams / existing DB infra |
| Audit | git history | `learn_audit` (trigger-enforced) |
| Default | ✅ recommended for new teams | when team already runs MySQL/PG |

Both modes share: hub model, weekly manual upload, central training Agent review, admin confirmation, `learn_private` stays local.
