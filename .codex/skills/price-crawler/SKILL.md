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
