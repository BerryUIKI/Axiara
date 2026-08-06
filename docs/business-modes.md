# Axiara — Business Modes & LangGraph Architecture

Status: **v0.2 draft** — baseline confirmed via PM-led discussion (2026-08-04). Naming: `main` (not master), `output/` (not out).

## 1. Data Layers & Write Permissions

| Layer | Role | Writable by | Readable by | Notes |
| --- | --- | --- | --- | --- |
| `main_db` (official price baseline) | High-weight baseline, source of truth | **Manual edit only** | All agents | Crawler/AI outputs can never overwrite; only serve as comparison |
| `learn_db` (learned reference) | AI-learned reference (materials, processes, cost rules) | Learning skill | All agents | Trained from historical quotes, old cost sheets, ledgers |
| `market_db` (market prices) | Crawled public market prices | Crawler skill (with user confirm) | All agents | Cleansed/normalized before insert |
| `user_input` | User tables / BOMs / documents | Transient per run | Processing agents | Not persistent business data |

## 2. The Four Modes

### Mode 1 — Edit & Archive (highest authority; only writer of main_db)
- **1.1 Standard manual edit** — user uploads/enters official price lists, processes, materials, notes → structured cleaning → write `main_db` (versioned, rollback-able). Highest weight, primary baseline source.
- **1.2 Auto edit** (produces reference/support data only, never writes main):
  - *Learning sub-mode*: input = historical quotes / old cost sheets / scattered ledgers → extract materials, processes, cost, note rules → train matching model → `learn_db`.
  - *Crawler sub-mode*: input = BOMs / industry sites / keyword direction → crawl public market prices → clean & denoise → `market_db`. Interrupt before insert: confirm with user.
- **1.3 Edit review** (attached to edit mode; cross-library validation):
  - Sources: `main_db` + `learn_db` + `market_db` three-way cross-check.
  - Detects: price anomalies, missing processes, stale prices.
  - Permissions: may trigger crawler/learning to supplement data, produces correction suggestions — **cannot write main_db**, outputs pending-review list for human confirmation.
  - Detection thresholds (tunable via `core/review/` `ReviewThresholds`, default): price deviation vs baseline ±25% → anomaly, ±50% → conflict (high); market staleness > 30 days; learn process rules without baseline coverage → missing process.

### Mode 2 — Single-item Detail Query
- Input: one material/product name.
- Logic: read `main_db` cost first, overlay `market_db` floating range.
- Output: standard cost + market reference quote + process notes.

### Mode 3 — Batch Table Query + Smart Quotation
- **3.1 Batch table fill**: input Excel/BOM table → auto-detect columns → match multi-library data → backfill cost & market price into cells.
- **3.2 Smart quotation** (user-uploaded cost list, manually enabled):
  - Before quoting, ask user whether they have constraints — **default constraints** (system-wide) and/or **project constraints** (per-project). If user specifies none → output **low / mid / high three tiers**.
  - Compute: baseline cost + market fluctuation + margin constraints → batch compliant quote plan.

### Mode 4 — Review (attached to query mode; post-hoc validation)
- Input: user's own cost/quote table.
- Logic: cross-validate against `main_db` + `market_db`, flag abnormal low/high prices and missing processes, output adjustment suggestion list.
- Detection thresholds (default): deviation vs baseline ±25% → abnormal low/high; no baseline → ±20% market reference band check; rows with no baseline/market reference → unvalidatable warning.

## 2b. Quote Template (default vs user-provided)

- Axiara is **open-source** — each company that forks it will have its own quote format.
- **Default template**: Agent designs and ships a default quote template in the workspace (used when no user template exists).
- **User template**: when a user provides their own quote template, Agent adapts to it on the fly (field mapping / layout).

## 2c. Smart Quote Constraint Flow

1. Before quoting, Agent asks the user whether constraints exist.
2. Two constraint layers: **default constraints** (system-wide defaults) and **project constraints** (per-project overrides).
3. If user specifies none → output **low / mid / high three-tier quote options** for the user to pick.

## 3. LangGraph Mapping

- **State** (`TypedDict`): `mode`, `user_input`, `main_db_ref` / `learn_db_ref` / `market_db_ref` (references/snapshots, NOT the DBs themselves), workflow flags.
- **Nodes**: `dispatcher`, `manual_edit`, `learn_agent`, `crawl_agent`, `edit_review`, `query_agent`, `batch_fill_agent`, `quote_agent`, `user_review_agent`.
- **Conditional edges**: mode dispatch at entry; review→crawl/learn cycles for data supplementation until threshold met.
- **`interrupt()` / human-in-the-loop**: crawler insert confirmation; multi-turn quote constraint dialogue; review suggestion confirmation.
- **Checkpointer**: batch job / long crawl resume after interruption; session persistence.
- **Subgraphs**: one per mode for isolation.
- **Permission enforcement**: hard rules in graph nodes **AND** enforced at the storage layer (defense in depth) — a node can only reach a DB through a storage interface that rejects forbidden writes.

## 4. Framework Conclusion

- **LangGraph** — only framework natively supporting: layered state isolation, conditional branch/cycle, interrupt-based multi-turn interaction, checkpointer persistence.
- **CrewAI** — rejects: linear pipeline, weak global state, no permission isolation, no native persistence (Flows adds some control but not enough).
- **AutoGen** — rejects: free-form conversational, no fixed orchestration, no layered state isolation.

## 5. Product Decisions (confirmed 2026-08-04, PM-led discussion)

| # | Question | Answer |
| --- | --- | --- |
| P1 | Who uses it | **Small team** — simple member permissions needed later, not now |
| P2 | Price sources | **Both** — supplier price lists (official, manual/upload) + public market data (crawler, reference) |
| P3 | Quote delivery | Agent produces files to `output/` directory; user decides how to use them (no interactive quote UI for now) |
| P4 | Market update frequency | **On-demand manual** — crawl when needed, not scheduled daily |
| P5 | Product form | **Agent workspace** — Agent works autonomously inside the workspace, choosing which data & skills to call; the 4 modes are capability/permission boundaries, not fixed UI flows |
| P6 | Main governance | Versioning + rollback for all main_db writes |
| P7 | Interactive client | REST API session mechanism (deferred until Axiara-Web) |
| P8 | Quote template | **Open-source friendly**: Agent ships a default template; adapts to user-provided templates on the fly |
| P9 | Quote constraints | Ask before quoting: default constraints + project constraints; none specified → low/mid/high three tiers |
| P10 | Team permissions | Default = admin only touches official lib; **not implemented in code** — handled later via SQL DB or Git repo permissions |

## 6. Naming Conventions (confirmed)

- `master` → **`main`** (official baseline dir)
- `out` → **`output`** (deliverables dir)
- `master_db` / `crawl_db` → **`main_db` / `market_db`**

## 7. Open Questions (minor, resolvable during implementation)

- **O1** — Terminology: in crawler sub-mode the confirm dialog says "sync reference market library" — resolved: it's `market_db` itself, the dialog is the insert confirmation.
- **O5** — Naming: Mode 1.3 "edit review" vs Mode 4 "review" are two different loops — keep both; 1.3 = internal quality gate, Mode 4 = user-facing validation.
- **O6** — Concurrency: single-user (local-first) now; multi-user via SQL/Git permissions later (per P10).
