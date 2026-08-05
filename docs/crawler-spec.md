# Axiara — Commodity Price Crawler Specification

Status: **v0.2** (2026-08-05) — design reference for SK-03 (`docs/skill-requirements.md`). v0.2 changes: trigger model confirmed (on-demand + optional weekly refresh, D-SK2), source registry defined (`docs/data-sources.md`, D-SK3/D-SK4), implementer split documented (WorkBuddy = spec/skill/config; external coding agent = engine/adapters). No code is written until the user confirms and storage layer exists.

Scope: **commodity / material market prices** (e.g. copper wire, aluminum, raw materials) fetched from **public** web sources. Financial-instrument quotes are out of scope (existing `westockdata` / `a-stock-data` skills cover those). Everything here feeds `data/market/` (**reference only**) — the crawler can **never** write `data/main/` (official baseline is human-only, business-modes §1).

---

## 1. Design Principles

1. **Reference-only.** Crawled data is comparison material. `main_db` can never be overwritten or silently influenced by crawler output.
2. **Human confirmation before insert.** Every batch lands in `data/market/` only after the user confirms the normalized result (LangGraph `interrupt()`, Mode 1.2 crawler sub-mode).
3. **Legal by default.** robots.txt, site ToS, rate limits, honest User-Agent. No login bypass, no paywall evasion, no personal data.
4. **Traceable & reproducible.** Every row keeps provenance (`source`, `url`, `fetched_at`); raw + normalized outputs both persist; re-runs are idempotent.
5. **On-demand + optional refresh.** Market updates are manually triggered; a low-frequency refresh is optional and **always confirm-gated** (D-SK2). Never automatic insertion.

---

## 2. Data Model

Crawler rows align with the official price-list field family so cross-library comparison works (`main` ↔ `market`).

### 2.1 Normalized row (per price observation)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | Canonical commodity/material name (normalized alias) |
| `spec` | string | no | Specification string, normalized (e.g. `1.5mm²`) |
| `unit` | string | yes | Unit after normalization (alias → canonical, e.g. `千克/公斤/KG` → `kg`) |
| `unit_price` | float | yes | Numeric price after currency normalization |
| `currency` | string | yes | ISO 4217 code (CNY / USD / EUR / JPY ...) |
| `effective_date` | date | yes | Date the price is valid as of (source-published or fetch date) |
| `note` | string | no | Free text (quality grade, region, tax note, etc.) |
| `source` | string | yes | Source id from the registry (`docs/data-sources.md`) |
| `url` | string | yes | Direct URL of the page the price was read from |
| `fetched_at` | datetime | yes | UTC timestamp of the fetch |
| `confidence` | enum | yes | `high` (explicit quote on page) / `medium` (derived/estimate) / `low` (unverified) |
| `raw` | string | no | Raw text as displayed on the page (for audit) |

### 2.2 Canonical name & unit normalization

- Maintain a **normalization dictionary** (YAML, skill-owned): aliases → canonical name (`铜线`/`copper wire`/`copper` → `copper-wire`), unit aliases (`千克`/`kg`/`KG`/`公斤` → `kg`, `米`/`m`/`M` → `m`).
- Unknown aliases are **kept raw and flagged** in the confirmation step — never guessed silently.
- Money formatting: strip thousands separators, normalize `¥`/`CNY`/`RMB` → `CNY`; non-ISO symbols are flagged.

---

## 3. Pipeline

```
trigger ──▶ 1. prepare ──▶ 2. fetch ──▶ 3. parse ──▶ 4. normalize ──▶ 5. dedup/denoise ──▶ 6. confirm ──▶ 7. store (data/market/)
             (adapter)     (http/browser)  (adapter)     (dict)          (rules)          (interrupt)      (JSON/YAML + manifest)
```

### 3.1 Prepare

- Resolve the target source from the **registry** (`docs/data-sources.md`); disabled sources are refused. Input: material name + optional keyword direction (from user BOM / query).
- Check robots.txt / terms once per source (cached in `.data/cache/`).
- Compose the source-specific query URL(s).

### 3.2 Fetch

- **HTTP-first** (`method: http`): `httpx` with sane timeouts (connect 10s / read 30s), retries with exponential backoff (3 tries: 1s / 5s / 15s), randomized per-source delays respecting `Crawl-delay`.
- **JS-rendered sources** (`method: browser`): built-in `agent-browser` capability (headless). Per-source policy from the registry, not default. Robots rules still apply.
- Honest `User-Agent` identifying the crawler (e.g. `Axiara-PriceBot/0.1 (+<repo url>)`).
- Failures: per-URL errors are logged, not fatal; the batch continues (partial-failure tolerance, §6).

### 3.3 Parse

- One **adapter per source** (CSS/XPath selectors or a named parser from the registry, §5).
- Output: raw candidate rows (name/spec/unit/price text as displayed, page URL, effective date).
- Parse failure on a page → logged with URL, row omitted, counted in the summary.

### 3.4 Normalize

- Apply §2.2 dictionaries; convert to the canonical row shape (§2.1).
- Effective date resolution: explicit page date > fetch date.
- Confidence assignment per §2.1.

### 3.5 Dedup / denoise

- Dedup key: `(name, spec, unit, currency, source)` — keep the most recent / highest-confidence row; identical duplicates collapsed.
- Anomaly filter: outside `[0.1×median, 10×median]` of the batch → quarantined to the confirmation diff with `low` confidence, never auto-dropped silently.

### 3.6 Confirm (human-in-the-loop)

- LangGraph `interrupt()` shows the user: summary (source, n rows, date range) + **diff vs existing `data/market/`** + flagged unknowns/quarantined rows.
- User choice: **accept** (insert) / **edit** (adjust rows, then insert) / **reject** (discard batch).
- Nothing is written to `data/market/` before this step. `data/main/` is never touched.

### 3.7 Store

- Write normalized batch to `data/market/<source>/<yyyymmdd>-<material>.json` (JSON for agent-generated artifacts, per D19/D20; YAML allowed for configs).
- Write raw capture next to it: `data/market/<source>/raw/<yyyymmdd>-<material>.json` (audit).
- Update SHA-256 manifest (`db_dump/`), append ledger entry (time, source, rows, accepted/rejected).

---

## 4. Scheduling (confirmed, D-SK2)

- **Default: on-demand manual** (P4). User says "fetch market price for X" → crawl once.
- **Optional weekly refresh**: an APScheduler job re-runs enabled sources on a weekly cadence and produces a **proposed diff** — still requires user confirmation before insert. **Never auto-insert.**
- PLAN.md D1 "periodic price fetch" is interpreted as the optional refresh above; automatic insertion is excluded by P4 (recorded in `docs/skill-requirements.md` §5 D-SK2).

---

## 5. Site Adapter Architecture

Registry lives in **`docs/data-sources.md`** (standard template + initial list). The crawler loads enabled sources from it; adapters are selectors or named parsers per source:

```yaml
# example entry (registry template, docs/data-sources.md)
smm:
  name: "上海有色网 (SMM)"
  region: cn
  category: metals
  base_url: https://www.smm.cn/
  method: http                  # http | browser — decided per source (D-SK4)
  robots_url: https://www.smm.cn/robots.txt
  legal: needs_review           # blocked until user sign-off
  enabled: false                # never true until legal confirmed
  selectors:                    # filled by coding agent during adapter work
    row: "table.prices tbody tr"
    name: "td:nth-child(1)"
    unit_price: "td:nth-child(4)"
    unit: "td:nth-child(3)"
  parse: ""                     # optional named parser override
  notes: "Metals spot prices; check ToS + anti-bot"
```

Rules:

- A source is **disabled by default** until robots check + `legal` confirmation (`public_market_data` auto-enables; anything else requires user sign-off).
- Selector-based adapters (CSS/XPath) cover most cases; a named parser override handles exotic layouts.
- Broken sources degrade to a logged failure, never a silent wrong price.
- Adding a source: follow `docs/data-sources.md` §3 usage flow.

---

## 6. Error Handling & Observability

| Failure | Behavior |
| --- | --- |
| Network / timeout | Retry with backoff (3 tries); then log + skip URL |
| robots.txt disallows | Skip source, log reason, do not retry until policy reviewed |
| HTTP 4xx / 5xx | Log status; page skipped; other pages continue |
| Parse failure | Row omitted, URL logged |
| Normalization unknown alias | Kept raw + flagged in confirmation diff (never guessed) |
| Source returns nothing | Batch empty → report to user, no write |
| Partial batch accepted | Only confirmed rows are stored; rest discarded with ledger note |
| Disabled source requested | Refused up front (registry check) |

All events: `ledger/` entries + per-run summary to the user (fetched / parsed / normalized / flagged / accepted).

---

## 7. LangGraph Integration

- **Node**: `crawl_agent` (business-modes §3). Input: `(mode=1.2, user_input, main_db_ref, market_db_ref)`.
- **Flow**: prepare → fetch → parse → normalize → **`interrupt()` confirm** → store → update state `market_db_ref`.
- **Checkpointer**: long crawls can be resumed after interruption (batch job persistence).
- **Permissions**: enforced in the node **and** at the storage layer (a crawler write to `data/main/` is rejected by the storage interface, defense in depth).
- **Edit review loop (Mode 1.3)**: crawler may be triggered to *supplement* reference data during review; output remains pending-review, never auto-accepted.

---

## 8. Deliverables, Owners & Roadmap

| # | Deliverable | Owner | Status |
| --- | --- | --- | --- |
| 1 | This spec (`docs/crawler-spec.md`) | WorkBuddy | ✅ v0.2 |
| 2 | Source registry (`docs/data-sources.md`) — template + initial list | WorkBuddy | ✅ v0.1 |
| 3 | SK-03 skill (WorkBuddy + Codex + Claude) bundling spec, registry, dictionaries | WorkBuddy | ⏳ after storage layer |
| 4 | Crawler engine + adapters + helpers (fetch/retry, robots check, parsers, normalization, dedup) | **External coding agent** | ⏳ roadmap: price fetch agent |
| 5 | Normalization dictionary YAML (initial draft) | WorkBuddy (draft) / coding agent (grow) | ⏳ with #3 |
| 6 | First enabled sources (recommend `mofcom-cif` + `indexmundi`) | Coding agent (adapters) + user (enable) | ⏳ OQ-4 |

## Open Questions (also tracked in skill-requirements.md)

- **OQ-4** — which sources to enable first (from `docs/data-sources.md`); recommend starting public + HTTP (`mofcom-cif`, `indexmundi`).
- **OQ-5** — browser-source scope beyond `alibaba-1688` / `made-in-china`; re-assess during adapter work.
- Resolved: OQ-1 (D-SK2 on-demand + weekly refresh) · OQ-2 (D-SK3 registry) · OQ-3 (D-SK4 method per source).
