---
name: axiara-onboarding
description: >
  Agent-driven first-time setup for the Axiara valuation workspace. Use when a
  fresh clone needs initialization, .data/ is missing or corrupted, or the user
  wants to change language / storage-sync / data source. Two paths: CREATE a new
  team/workspace (guided Q&A, everything pre-filled from inference — currency by
  language, timezone by OS, date/quote formats — user confirms or edits) or JOIN
  an existing team/shared workspace (apply the team workspace.config.yaml
  template, near-zero Q&A, pull learn_shared). Maps answers to
  scripts/init-data.sh flags, runs the script, verifies, orients to
  anti-tampering. Triggers: "init", "set up", "onboarding", "first use",
  "reinstall", "create workspace", "join team", "change language / storage /
  data source".
---

# Axiara Onboarding

Bring a fresh Axiara clone to a working, verified state. Axiara is open-source:
users either **create** a team/workspace or **join** an existing one by reusing
its config. The user never reads `docs/init.md` — the Agent asks the questions,
in the user's language, then runs the script. Docs stay English (D9);
conversation happens in the user's language (D21). Design: `docs/workspace-config.md`.

## When to use

- First use of a new workspace.
- `.data/` wiped or corrupted (back up `local_config/` first — it is NOT regenerated).
- User wants to change language / storage-sync / data source.

## Step 1 — Ask: create or join?

**Create** (new team/workspace) → proceed to Step 2.
**Join** (existing team / shared workspace) → ask only for the team repo URL (or a
shared config file) → **Step 4 (apply template)**. Everything else comes from the template.

## Step 2 — Create: core questions (not inferable)

1. **Language** — output language for quotations/documents: `en zh-CN zh-TW ja ko de fr es pt-BR ru`.
2. **Team sync?** — no (personal) → `sqlite`; yes → ① Text+Git → `csv` ② SQL server → `mysql|mariadb|postgresql` + DSN.
3. **Data source** — local files / team repo (URL) / no data yet.

## Step 3 — Create: pre-filled inference review

Infer and **pre-fill** the rest (ask once, not per field):

| Field | Inferred from | Default mapping |
| --- | --- | --- |
| `currency` | language | zh-CN→CNY · zh-TW→TWD · ja→JPY · ko→KRW · de/fr/es→EUR · pt-BR→BRL · ru→RUB · en→USD |
| `timezone` | system (OS) | e.g. `Asia/Shanghai` |
| `date_format` | region | `YYYY-MM-DD` |
| `quote_currency` | currency | same as currency (editable) |
| `quote_decimals` | currency | 2 (JPY→0) |
| `industry` (optional) | none | blank |

Show the full list → "keep or change?" → one confirmation. Then optionally
"export these settings as a team template?" (recommended: yes, so others can join).

## Step 4 — Run & apply

**Create**: map answers to flags and run:

```bash
bash scripts/init-data.sh \
  --language <lang> --sync-mode <none|git|sql> --backend <sqlite|csv|mysql|mariadb|postgresql> \
  --data-source <local_file|team_repo|none> [--repo-url <url>] [--db-dsn <dsn>]
```

(Omitted flags keep existing config; re-run backs up to `config.bak`; no-flags runs never touch existing config.)

**Join**: clone/pull `store/` → read `store/workspace.config.yaml` → apply team values into
`local_config/config`; ask only local-only items (paths, local cache). Then pull
`learn_shared` ("synced N shared rules") — see `docs/learn-sync.md`.

## Step 5 — Verify

- `.data/` layout present: `store/ cache/ ledger/ db_dump/ local_config/`.
- `local_config/config` written (`[data_repo] [git] [app] [storage] [workspace]` sections; new fields currency/timezone/date_format/quote_*).
- `store/` synced (or the warning explained); `learn_shared` pulled on join.
- Baseline SHA-256 manifest initialized in `db_dump/` (on first official-baseline import).

<<<<<<< Updated upstream
**Verification script:**

```bash
python skills/axiara-onboarding/scripts/verify_setup.py
```

Checks: `.data/` structure ✓ · config file + required sections ✓ · store sync status ✓ · manifest initialization ✓.

## Step 6 — Anti-tampering orientation

- Official baseline `data/main/` is **human-edit only**; agents never write it.
- Unexpected baseline change → **review mode**: show diff, ask "did you change this?", only continue after confirmation. Never silently continue.
=======
## Step 6 — Anti-tampering orientation

- Official baseline `data/main/` is **human-edit only**; agents never write it.
- Unexpected baseline change → **review mode**: show diff, ask "did you change this?", only continue after confirmation.
>>>>>>> Stashed changes
- Detect: manifest + `git status`; Recover: git history / `db_dump/` snapshots / SQLite cache; Audit: `ledger/` + git log.

## Examples

### Example 1: Create — personal mode (SQLite)

```bash
# User answers (in their language):
# 1. Language: zh-CN
# 2. Team sync? No (personal)
# 3. Data source: none (fresh start)
# Pre-filled & confirmed: currency=CNY, timezone=Asia/Shanghai, date_format=YYYY-MM-DD

bash scripts/init-data.sh --language zh-CN --sync-mode none --backend sqlite --data-source none

# Result:
# ✓ .data/ created with SQLite backend
# ✓ local_config/config written (language=zh-CN, sync_mode=none, backend=sqlite, currency=CNY)
# ✓ Ready to import price lists
```

### Example 2: Join — team mode (CSV + git)

```bash
# User provides team repo: https://github.com/team/axiara-data.git
# Agent applies store/workspace.config.yaml (currency/timezone/backend from template)

bash scripts/init-data.sh --sync-mode git --backend csv --data-source team_repo --repo-url https://github.com/team/axiara-data.git

# Result:
# ✓ .data/ created with CSV backend
# ✓ store/ cloned; learn_shared pulled (N shared rules)
# ✓ Template applied; only local paths were asked
# ⚠ Push requires manual confirmation (never automatic)
```

### Example 3: Changing configuration

```bash
# User wants to change language from en to zh-CN
bash scripts/init-data.sh --language zh-CN

# Result:
# ✓ Existing config backed up to config.bak
# ✓ language updated to zh-CN
# ⚠ Other settings preserved (no-flags runs never touch existing config)
```

## Troubleshooting (quick)

| Symptom | Fix |
| --- | --- |
| `store/` empty | `data_repo.url` not set — pass `--repo-url` and re-run |
| Join: template missing | team repo has no `workspace.config.yaml` — ask user to point to the config file or create |
| SQL connection fails | wrong `--db-dsn` — check host/port/credentials |
| `.data/` partly deleted | safe to recreate; only `local_config/` can't be regenerated |

<<<<<<< Updated upstream
## Common Mistakes

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Forgot to backup `local_config/` before reinstall | Private settings lost | `local_config/` is NOT regenerated — always backup before wiping `.data/` |
| Re-running with wrong flags | Config overwritten unexpectedly | Use no-flags run to check status; always specify flags explicitly when changing |
| Team repo URL wrong | `store/` empty after sync | Check `--repo-url` format; verify repo exists and is accessible |
| SQL DSN format wrong | Connection fails | Use standard format: `mysql://user:pass@host:port/dbname` |

## See Also

- **Configuration schema**: `skills/axiara-onboarding/references/config_schema.md`
- **Verification script**: `skills/axiara-onboarding/scripts/verify_setup.py`
- **Config & templates**: `docs/workspace-config.md`
- **Initialization guide**: `docs/init.md`
- **Data directory contract**: `.data.template/README.md`
- **Full guide**: `docs/init.md`
=======
Full guide: `docs/init.md`. Config & templates: `docs/workspace-config.md`. Runtime layout: `.data.template/README.md`.
>>>>>>> Stashed changes
