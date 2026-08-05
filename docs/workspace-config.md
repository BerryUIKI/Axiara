# Axiara — Workspace Configuration & Templates

Status: **v0.1** (2026-08-05) — design for the open-source onboarding model. Axiara is open-source: each company/team that forks it has its own conventions. Users should be able to (a) create a team/workspace by answering a few questions, and (b) join an existing team/workspace by reusing its config — no repeated Q&A. Updates SK-01 (`axiara-onboarding`). Implementation of new fields in `scripts/init-data.sh` / config is a coding-agent task after design confirmation.

## 1. Two Entry Paths

| Path | Who | Flow | Questions |
| --- | --- | --- | --- |
| **Create** | First-time user starting a team/workspace | Guided onboarding: everything is **pre-filled from inference**, user confirms or edits → config written → optional export as team template | A few, all pre-filled |
| **Join** | User joining an existing team/shared workspace | Provide team repo URL (or shared config file) → clone/pull → **apply the team template** → only local-only items are asked | Near-zero (local paths only) |

Create once, share the template; join is one step.

## 2. Pre-filled Inference (ask nothing the user hasn't confirmed)

Instead of asking every question, Axiara **infers and pre-fills**, then shows a review list: "here's what I set up — anything to change?" The user confirms or edits. Inference sources: the language the user chose (D21) + system information (OS timezone/locale).

| Field | Inferred from | Default mapping |
| --- | --- | --- |
| `language` | user's choice | en / zh-CN / zh-TW / ja / ko / de / fr / es / pt-BR / ru |
| `currency` | language | zh-CN→CNY · zh-TW→TWD · ja→JPY · ko→KRW · de/fr/es→EUR · pt-BR→BRL · ru→RUB · en→USD |
| `timezone` | system (OS) | e.g. `Asia/Shanghai` — pre-filled, editable |
| `date_format` | language/region | ISO `YYYY-MM-DD` default (editable) |
| `quote_currency` | currency | same as `currency` (editable; e.g. quote in USD while costs in CNY) |
| `quote_decimals` | currency | 2 (JPY→0) — editable |
| `industry` (optional) | none | left blank; used only to pick a default quote-template flavor |
| `sync_mode` / `backend` / `data_source` | core questions (not inferable) | asked as today (SK-01) |

Interaction: **show the full pre-filled list → "keep or change?" → one confirmation.** No field-by-field interrogation.

## 3. Question Set (Create path)

- **Round 1 — core (required, not inferable):** need team sync? → `sync_mode` (`none|git|sql`) → `backend` (`sqlite|csv|mysql|mariadb|postgresql`) → data source (`local_file|team_repo|none` → repo URL / DSN).
- **Round 2 — optimization (all pre-filled, confirm-or-edit):** currency, timezone, date_format, quote_currency, quote_decimals, industry.
- Optional at the end: "export these settings as a team template?" (see §4).

## 4. Configuration Template Mechanism

- **Create** → the confirmed answers produce the workspace config **and can be exported as a shareable template** (`workspace.config.yaml`).
- **Join** → the template in the team repo (`store/workspace.config.yaml`, or passed as a file) is applied directly; only local-only items (paths, local cache) are asked.
- Template contents (shareable, safe): `[app]` language/currency/timezone/date_format/quote settings, `[data_repo]`, `[storage]`, quote-template preference, optional industry dictionary seed.
- **Never in a template**: `local_config` private items (git identity, credentials, local paths).
- Official default template ships with Axiara (mirrors D12's "Agent ships a default quote template"); teams overwrite with their own.
- Versioned: `template_version`; a join re-applies the latest template, local overrides are kept in `local_config` (no silent re-clobber).

## 5. Join Flow (detailed)

1. User provides team repo URL (or a shared config file).
2. Agent clones/pulls `store/`, reads `store/workspace.config.yaml`.
3. Applies team values → writes `local_config/config`; asks only local-only items.
4. Verifies `.data/` layout + pulls `learn_shared` (see `docs/learn-sync.md`).
5. Local edits never write back to the team template unless the user explicitly exports a new template version.

## 6. Config Schema (new fields)

```ini
[app]
language = en
sync_mode = git
backend = csv
data_source = team_repo
currency = CNY          # NEW
timezone = Asia/Shanghai # NEW
date_format = YYYY-MM-DD # NEW
quote_currency = CNY     # NEW
quote_decimals = 2       # NEW
industry =               # NEW (optional)

[workspace]
template_id =            # NEW (join: applied template)
template_version =       # NEW
```

## 7. Open Questions

- **OQ-C1** — Template location: `store/workspace.config.yaml` (team repo root) vs a dedicated `templates/` subdir — recommend repo root for discoverability.
- **OQ-C2** — Industry dictionary seed in template: useful or premature? (Only matters when default quote template gains industry flavors.)
- **OQ-C3 — RESOLVED (2026-08-05)**: "export template" is **automatic** — every created workspace has a `workspace.config.yaml` from day one (join must have something to apply).
