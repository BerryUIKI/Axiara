---
name: price-crawler
description: >
  Fetch public market prices for commodities/materials into the Axiara workspace
  (data/market/, reference only). Use when the user says "fetch current market
  price for X", a weekly market-reference refresh runs, or review mode needs
  supplementary market data. Enforces robots protocol, runs a
  prepare → fetch → parse → normalize → dedup → confirm → store pipeline, and
  NEVER writes data/main/; every insert into data/market/ is user-confirmed and
  traceable. Design: docs/crawler-spec.md. Sources: docs/data-sources.md.
  Triggers: "fetch market price", "crawl", "market price for X",
  "refresh market reference".
---

# Commodity Price Crawler

Fetch public market prices for commodities/materials, normalize them, and land
them in `data/market/` (**reference only** — the official baseline `data/main/`
is human-edit only and can never be touched by crawler output).

## When to use

- User: *"fetch current market price for X"* (on-demand, default).
- Optional weekly refresh job (produces a **proposed diff** — still confirmed).
- Review mode (Mode 1.3) supplementing market reference data.

## Examples

### Example 1: On-demand price fetch

```bash
# User requests market price
axiara fetch copper-wire

# Agent runs crawler pipeline:
# 1. Prepare → resolve sources from registry (smm, mofcom-cif)
# 2. Fetch → httpx with retries, respect robots.txt
# 3. Parse → extract prices using adapters
# 4. Normalize → apply normalization dictionary
# 5. Dedup → remove duplicates
# 6. CONFIRM → show diff to user

# Confirmation screen:
# Source: smm (Shanghai Metals Market)
# Date range: 2026-08-05
# Rows: 5 prices fetched
#
# + copper-wire 1.5mm²: CNY 68.5/kg
# + copper-wire 2.5mm²: CNY 65.2/kg
# ~ aluminum A00: CNY 18500/ton (was 18200)
#
# Accept? [y/n/edit]: y
# ✓ Stored to data/market/smm/20260805-copper-wire.json
```

### Example 2: Robots.txt check

```bash
# Check if source allows crawling
python skills/price-crawler/scripts/check_robots.py https://www.smm.cn/

# Output:
# ✓ ALLOWED - robots.txt permits crawling
# Crawl-delay: 2 seconds
```

### Example 3: Disabled source

```bash
# Attempt to fetch from disabled source
axiara fetch copper-wire --source unverified-site

# Output:
# ✗ Source 'unverified-site' is disabled
# Reason: legal status is 'needs_review'
# Action: User must approve source before enabling
```

## Configuration Files

### Normalization Dictionary

Maps aliases to canonical names/units:
- `skills/price-crawler/config/normalization.yaml`

### Source Registry

List of approved data sources:
- `skills/price-crawler/config/sources.yaml`

### Adapter Selectors

Per-source parsing rules:
- `skills/price-crawler/config/adapters.yaml`

### Crawler Settings

Global crawler configuration:
- `skills/price-crawler/config/settings.yaml`

## Pipeline (7 steps)

```
prepare → fetch → parse → normalize → dedup/denoise → CONFIRM → store
```

1. **Prepare** — resolve source from the registry (`docs/data-sources.md`);
   **disabled sources are refused**. Check robots.txt per source (cached in
   `.data/cache/`). Compose query URL(s) from material name + keyword direction.
2. **Fetch** — `method: http` → httpx (timeouts, 3 retries with backoff, respect
   `Crawl-delay`); `method: browser` → built-in browser capability (JS-rendered
   pages). Honest User-Agent. Per-URL failures are logged, not fatal.
3. **Parse** — per-source adapter (selectors or named parser from the registry).
   Raw rows keep their page URL + effective date.
4. **Normalize** — apply the normalization dictionary (name/unit aliases →
   canonical); currency → ISO. Unknown aliases are **kept raw and flagged**, never
   guessed.
5. **Dedup / denoise** — dedup on `(name, spec, unit, currency, source)`; anomaly
   filter `[0.1×median, 10×median]` quarantines to the confirmation diff.
6. **CONFIRM (human-in-the-loop)** — show summary + diff vs existing
   `data/market/` + flagged rows. User: accept / edit / reject. **Nothing is
   written before this step.**
7. **Store** — normalized batch → `data/market/<source>/<yyyymmdd>-<material>.json`;
   raw capture → `data/market/<source>/raw/`; update SHA-256 manifest in
   `db_dump/`; append `ledger/` entry.

## Hard rules

- **Never write `data/main/`.** Storage layer rejects crawler writes there
  (defense in depth).
- **Robots protocol is mandatory** for every source — no bypass, no login-bypass,
  no paywall evasion.
- **Insertion requires user confirmation**, on-demand and for the weekly refresh.
- Every row carries provenance: `source, url, fetched_at, confidence, raw`.

## Implementation status

The engine + adapters are **implemented by an external coding agent** following
`docs/crawler-spec.md` (this skill is the operating manual). Until the engine
exists, this skill serves as the spec for the crawl behavior — do not hand-roll
one-off scrapes that bypass the registry/robots checks.

## Configuration Quick Reference

| Config File | Purpose |
| --- | --- |
| `config/normalization.yaml` | Alias → canonical name/unit mappings |
| `config/sources.yaml` | Registry of approved data sources |
| `config/adapters.yaml` | Per-source CSS/XPath selectors |
| `config/settings.yaml` | HTTP retries, delays, timeouts |

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/check_robots.py` | Verify robots.txt compliance |
| Fetch + parse + normalize | Implemented by coding agent (C2) |

## See Also

- **Crawler spec**: `docs/crawler-spec.md`
- **Data sources**: `docs/data-sources.md`
- **Normalization config**: `skills/price-crawler/config/normalization.yaml`
- **Example output**: `skills/price-crawler/assets/example_market.json`
