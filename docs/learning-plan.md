# Axiara — Learning Data & Training Plan (learn_db)

Status: **v0.1 draft** (2026-08-05) — plan for building the learned-reference library (`learn_db`). References: `docs/business-modes.md` (Mode 1.2 learning sub-mode), `docs/init.md` (learn over time), `docs/skill-requirements.md` (SK-02 csv-data-import). No implementation starts until the user confirms the plan and storage layer exists.

**What "training" means here**: turning historical quotes, invoices, old cost sheets and correction records into structured, reviewable rules in `data/learn/` — not a black-box ML model. Everything is explainable, versioned, and human-gated.

> User-facing counterpart: **`docs/training-scenarios.md`** — imagined real-user training situations (S1–S13) mapped to features and phase priorities.
> Multi-user sync: **`docs/learn-sync.md`** — hub model: personal library → weekly upload → central training Agent review → public library.

---

## 1. Goals & Non-Goals

Goals:
- Build a learned reference that lets Axiara **suggest** material costs, process costs, and default pricing tiers from history.
- Make every learned rule **traceable** (source records) and **reviewable** (audit + rollback).
- Close the loop: approved/corrected quotations feed back into learning (incremental).

Non-goals (hard lines):
- **learn_db never writes `data/main/`** (official baseline is human-only; learned output is reference, business-modes §1).
- No autonomous trading on learned prices — all learned suggestions go through review (Mode 1.3 / Mode 4).
- No opaque model artifacts as the primary product — rules first, models as an optional layer.

## 2. Training Data Sources (ranked by signal value)

| # | Source | Content | Signal | Ingestion path |
| --- | --- | --- | --- | --- |
| S1 | **Approved quotations** | Final quoted prices the user shipped | High (positive samples, real margins) | User upload / `output/` archive → SK-02-style import |
| S2 | **Corrected quotations** | Quote vs. final-approved diff (manual fixes) | **Highest** (error-correction pairs) | Same upload flow; flagged `correction` |
| S3 | **Invoices / order sheets** | Real transaction prices | High | SK-02 learning path (Mode 1.2) |
| S4 | **Old cost sheets / BOMs** | Structured material + process + cost breakdown | High (structure already there) | CSV import |
| S5 | **`data/main/` official baseline** | Authoritative unit prices | Anchor/label only — **never training input** that overrides itself | Read-only reference |
| S6 | **`data/market/` market prices** | Crawled reference prices | Feature (context window), low weight | Read-only reference |

Rule: S1–S4 are **training input**; S5/S6 are **anchors for validation**, never learning sources that can overwrite official data.

## 3. Data Governance

- **Landing**: imported files → `data/learn/raw/<source>/<date>-<name>.csv|json` (immutable copies, never edited in place).
- **Cleaning** (reuses SK-02 `csv-data-import` validation + the crawler normalization dictionary):
  - Field alignment to the price-list family (`name,spec,unit,unit_price,currency,effective_date,note` + provenance).
  - Dedup on `(name, spec, unit, currency, source)`.
  - Unit/currency normalization via the shared dictionary (alias → canonical).
  - Anomaly quarantine: outside `[0.1×median, 10×median]` of batch → flagged, not auto-dropped.
  - Every cleaned row keeps `source_row_id` → traceable to raw.
- **Versioning & integrity**: cleaned output → `data/learn/clean/`; SHA-256 manifest updated in `db_dump/`; ledger entries per ingest batch.
- **Permissions**: learning writes only `data/learn/`. Storage layer rejects any learn→main write (defense in depth).

## 4. Learned Artifacts (what lives in learn_db)

Directory: `data/learn/`

| Dir | Artifact | Format | Content |
| --- | --- | --- | --- |
| `clean/` | Cleaned standard rows | CSV | Normalized historical observations |
| `rules/` | **Material rules** | YAML | name/spec aliases → canonical material ID (shared with crawler dict) |
| `rules/` | **Process-cost rules** | YAML | process (cutting/welding/plating…) → unit processing fee, loss rate, yield |
| `rules/` | **Cost-breakdown rules** | YAML | material + labor + loss + processing → total cost (component distribution) |
| `rules/` | **Pricing rules** | YAML | approved price vs. cost → markup distribution; default low/mid/high tiers (Mode 3.2) |
| `stats/` | Statistical baseline | JSON | Per `(material, process)` median / quartiles / n — rebuildable from `clean/` |
| `models/` | Similarity index | JSON/binary cache | Optional L2 matching index — rebuildable, never hand-edited |

## 5. Learning Mechanism (three layers, shallow → deep)

**L1 — Statistical baseline (ship first).** Aggregate cleaned rows per `(material, process)`:
median, 25/75 percentiles, count. Output = the low/mid/high tier defaults. Explainable, human-reviewable, no model.

**L2 — Similarity matching (optional).** For a query material not in the stats table: normalize → find nearest historical samples (alias-aware similarity / vector index) → return the matched price window with `confidence` + matched source rows. Pure lookup — never a learned price of its own.

**L3 — LLM rule extraction (later).** Agent reads unstructured history (old cost-sheet notes, process annotations, correction comments) and proposes rules (material aliases, process-cost entries, markup patterns) → **human confirmation before the rule enters `rules/`**. Corrections to proposed rules also become training signals (S2).

All layers emit `confidence` and `source_refs`; nothing auto-inserts without review (Mode 1.3 gate).

## 6. Validation & Quality Gates

- **Holdout backtest**: time-split (e.g. train on older 80%, validate on recent 20% of approved quotes) → compare learned suggestion vs. actual approved price → report MAE / error distribution. Runs at each learning batch.
- **Three-way cross-check (Mode 1.3 edit review)**: learned suggestion vs. `data/main/` official vs. `data/market/` reference → anomalies flagged to the user.
- **Drift monitor**: if learned suggestions systematically deviate from newly approved quotes (> threshold), flag "retrain suggested" — no silent staleness.
- **Quality gate for tiers**: low/mid/high defaults only promoted after ≥ N observations per `(material, process)` (e.g. N≥5) and pass backtest.

## 7. Feedback Loop (incremental learning)

- Every approved quotation → ingested (S1); every manual correction → ingested with `correction` flag (S2, highest weight).
- Ledger records the loop events; stats/models are **rebuildable** (idempotent from `clean/`), so incremental = re-run pipeline on new rows.
- Correction weight: S2 rows count double in stats and always refresh the tier defaults for that `(material, process)`.

## 8. Implementation Roadmap

| Phase | Deliverable | Owner | Depends on |
| --- | --- | --- | --- |
| 0 | Ingest gate for S1–S4 (import + landing + manifest) | WorkBuddy skill (extend SK-02) + coding agent (storage) | Storage layer, SK-02 |
| 1 | Cleaning pipeline + L1 stats baseline → `learn_db` v1 (rules + stats) | Coding agent (pipeline code); WorkBuddy (dictionary draft) | Phase 0 |
| 2 | L2 similarity matching + backtest framework | Coding agent | Phase 1 |
| 3 | L3 LLM rule extraction + review UI flow | WorkBuddy (agent workflow) + coding agent (helpers) | Phase 1 |
| 4 | Feedback loop (approved/corrected quote → `learn_private`) + weekly upload flow (hub model, `docs/learn-sync.md`) | Coding agent (APScheduler + storage) | Phase 2, quote generator |
| 5 | Drift monitor + retrain prompts | Coding agent | Phase 2 |

## 9. Open Questions

- **OQ-L1** — First training batch: does the user have historical quotes/invoices/cost sheets available now, or do we start with an empty `learn_db` and grow it?
- **OQ-L2** — Scope of materials: start with a few focus materials (recommended) vs. full catalog?
- **OQ-L3** — Pricing rules (markup tiers): auto-suggested only, or allowed to seed the quote default constraints (Mode 3.2 asks first anyway)?
- **OQ-L4 — DESIGNED (2026-08-05)**: sync splits into `learn_shared` (team, git/sql) vs `learn_private` (local, never synced) — full design in `docs/learn-sync.md`. Confirm OQ-LS1..3 when implementing.
- **OQ-L5** — N threshold for tier promotion (suggested N≥5): tune after first backtest.
