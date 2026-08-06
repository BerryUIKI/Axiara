# Axiara — Data Source Registry (Template + Initial List)

Status: **v0.1** (2026-08-05) — standard template for commodity price sources + an initial recommended list (domestic CN + global). References `docs/crawler-spec.md` (SK-03). All sources **must respect the robots protocol**; no source is enabled until its `legal` status is confirmed.

This file is the **registry template**. Adding a source = copy the template, fill fields, run the robots check, set `enabled: false` until legal confirmed. An agent (WorkBuddy for config, coding agent for adapter code) fills `selectors`/`parse` during adapter work.

## 1. Source Template

```yaml
<source-id>:                       # lowercase-hyphen, e.g. "smm"
  name: "<display name>"           # e.g. "上海有色网 SMM"
  region: cn | global | us | eu
  category: metals | energy | agri | chemicals | b2b-marketplace | exchange | government
  base_url: "<https url>"
  method: http | browser           # http = plain HTTP (httpx); browser = JS-rendered, use agent-browser
  robots_url: "<url of robots.txt>" # must be fetched & reviewed BEFORE any request
  legal: public_market_data | needs_review | paid_requires_license
  enabled: false                   # NEVER true until legal confirmed
  selectors:                       # filled during adapter work (CSS/XPath)
    row: ""
    name: ""
    spec: ""
    unit_price: ""
    unit: ""
    effective_date: ""
  parse: <named-parser-or-empty>   # override for exotic layouts
  notes: "<risk / license / data freshness notes>"
```

### 1.1 Field rules

- **`method` decision (OQ-3, decided)**: plain HTML / light-JS static tables → `http` (httpx). Heavy JS-rendered dynamic pages (B2B marketplaces, SPA sites) → `browser` (built-in `agent-browser`). Even for `browser`, robots rules still apply (meta robots / robots.txt).
- **`legal` decision (OQ-2, decided)**: `public_market_data` (government statistics, exchange delayed data, sites whose ToS allow non-commercial reference use) → auto-enable after robots check. `needs_review` (ToS ambiguous, aggressive anti-bot) → blocked until user signs off. `paid_requires_license` (paywalled data, vendor APIs) → blocked unless a license exists.
- **Robots protocol is mandatory**: fetch `robots.txt` once per source (cache in `.data/cache/`), respect `Disallow` paths and `Crawl-delay`; re-check on each enable/update. Never bypass, never login-bypass, never paywall-evade.
- **`enabled` defaults to `false`** — a source only flips to `true` after robots + legal review. The crawler refuses to touch disabled sources.

## 2. Initial Recommended Sources (draft — user picks which to enable first, OQ-4)

> All entries below are **candidates**, not enabled. `legal` is my best-effort assessment; the robots check and any licensing terms must be confirmed before use. Selector details left blank for adapter work.

### Domestic (CN)

| id | name | category | method | legal | notes |
| --- | --- | --- | --- | --- | --- |
| `mofcom-cif` | 商务部商务预报 (MOFCOM) | government | http | public_market_data | Official commodity price reporting; robots-friendly; ideal first source |
| `ndrc-price` | 发改委价格监测中心 | government | http | public_market_data | Official price monitoring; public |
| `smm` | 上海有色网 (SMM) | metals | http | needs_review | Metals spot prices (Cu/Al/etc.); check ToS + anti-bot; some pages JS-heavy |
| `ccmn` | 长江有色金属网 | metals | http | needs_review | Metals spot quotes; static tables mostly |
| `100ppi` | 生意社 (100ppi) | agri/chemicals | http | needs_review | Bulk commodity spot prices; large catalog |
| `mysteel` | 我的钢铁网 (Mysteel) | metals | http | paid_requires_license | Steel prices; core content paywalled — only free previews if ToS allows |
| `cngold` | 金投网 (Cngold) | metals/energy | http | needs_review | Precious metals & bulk commodities reference |

### Global

| id | name | category | method | legal | notes |
| --- | --- | --- | --- | --- | --- |
| `indexmundi` | IndexMundi | agri/energy/metals | http | public_market_data | Clean static commodity price tables; ideal global first source |
| `infomine` | InfoMine | metals/mining | http | public_market_data | Mining commodity prices; static |
| `lme` | London Metal Exchange | metals (exchange) | http | needs_review | Official delayed prices; ToS review required; possible structured data |
| `tradingeconomics` | TradingEconomics | macro/commodities | http | needs_review | Free tier limited; API paid — scrape only what ToS allows |
| `alibaba-1688` | 1688 / Alibaba | b2b-marketplace | browser | needs_review | Heavy JS + strict anti-bot; quoted merchant prices are indicative only |
| `made-in-china` | Made-in-China | b2b-marketplace | browser | needs_review | Heavy JS; indicative quotes |

## 3. Usage Flow (agent adds a source)

1. Copy the template into the registry config (skill-owned YAML, versioned).
2. Run robots check for `robots_url` → record result in the source entry.
3. Assess `legal` per §1.1. If not `public_market_data` → keep `enabled: false`, flag for user sign-off.
4. If enabled: implement/validate selectors (or named parser) — **coding agent** writes the adapter code; **WorkBuddy** keeps the registry config.
5. Verify a dry-run fetch + normalization on one page before enabling.

## 4. Open Items

- **OQ-4** — user picks the first sources to enable (recommend starting with `mofcom-cif` + `indexmundi`: both public, both HTTP).
- **OQ-5** — whether any candidate needs `browser` beyond `alibaba-1688` / `made-in-china` — re-assess during adapter work.
- Adapter selectors for each enabled source: filled by coding agent, reviewed before enable.
