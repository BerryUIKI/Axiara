---
name: axiara-onboarding
description: >
  Agent-driven first-time setup for the Axiara valuation workspace. Use when a
  fresh clone needs initialization, .data/ is missing or corrupted, or the user
  wants to change language / storage-sync / data source. Conducts the onboarding
  Q&A in the user's language, maps answers to scripts/init-data.sh flags, runs
  the script, verifies the result, and orients to the anti-tampering flow.
  Triggers: "init", "set up", "onboarding", "first use", "reinstall",
  "change language / storage / data source".
---

# Axiara Onboarding

Bring a fresh Axiara clone to a working, verified state. The user never reads
`docs/init.md` — the Agent asks the questions, in the user's language, then runs
the script. Docs stay English (D9); conversation happens in the user's language (D21).

## When to use

- First use of a new workspace.
- `.data/` wiped or corrupted (back up `local_config/` first — it is NOT regenerated).
- User wants to change language / storage-sync / data source.

## Step 1 — Ask (in the user's language)

1. **Language** — which language should Axiara output (quotations, ledgers, documents)?
   Options: `en zh-CN zh-TW ja ko de fr es pt-BR ru`.
2. **Team sync?** — one question, everything follows (decision tree from `docs/init.md`):
   - No (personal) → backend `sqlite`.
   - Yes → ① Text + Git → backend `csv` (no server) · ② SQL server → `mysql|mariadb|postgresql` + connection string.
3. **Data source** — local files (price lists to import) / team repo (enter URL) / no data yet.

## Step 2 — Map to flags and run

```bash
bash scripts/init-data.sh \
  --language <en|zh-CN|zh-TW|ja|ko|de|fr|es|pt-BR|ru> \
  --sync-mode <none|git|sql> \
  --backend <sqlite|csv|mysql|mariadb|postgresql> \
  --data-source <local_file|team_repo|none> \
  [--repo-url <url>]   # when team repo
  [--db-dsn <dsn>]     # when SQL
```

- Omitted flags keep existing config; re-running with flags backs up to `config.bak` first.
- **No-flags runs never touch an existing config** (safe for agents/CI).
- `store/` sync failure is a warning, not fatal.

## Step 3 — Verify

- `.data/` layout present: `store/ cache/ ledger/ db_dump/ local_config/`.
- `local_config/config` written (`[data_repo] [git] [app] [storage]` sections).
- `store/` synced (or the warning explained to the user).
- Baseline SHA-256 manifest initialized in `db_dump/` (created on first official-baseline import).

## Step 4 — Anti-tampering orientation

- Official baseline `data/main/` is **human-edit only**; agents never write it.
- Unexpected baseline change → enter **review mode**: show the diff, ask "did you change this?", only continue after confirmation. Never silently continue.
- Detect: manifest + `git status`; Recover: git history / `db_dump/` snapshots / SQLite cache; Audit: `ledger/` + git log.

## Examples

### Example 1: Personal mode (SQLite)

```bash
# User answers (in their language):
# 1. Language: zh-CN
# 2. Team sync? No (personal)
# 3. Data source: none (fresh start)

# Agent runs:
bash scripts/init-data.sh --language zh-CN --sync-mode none --backend sqlite --data-source none

# Result:
# ✓ .data/ created with SQLite backend
# ✓ local_config/config written with language=zh-CN, sync_mode=none, backend=sqlite
# ✓ Ready to import price lists
```

### Example 2: Team mode (CSV + git)

```bash
# User answers:
# 1. Language: en
# 2. Team sync? Yes → Text + Git
# 3. Data source: team repo → https://github.com/team/axiara-data.git

# Agent runs:
bash scripts/init-data.sh --language en --sync-mode git --backend csv --data-source team_repo --repo-url https://github.com/team/axiara-data.git

# Result:
# ✓ .data/ created with CSV backend
# ✓ store/ cloned from team repo
# ✓ local_config/config written with git sync settings
# ⚠ Note: Push requires manual confirmation (not automatic)
```

### Example 3: Changing configuration

```bash
# User wants to change language from en to zh-CN
# Agent runs with --language flag:

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
| SQL connection fails | wrong `--db-dsn` — check host/port/credentials |
| `.data/` partly deleted | safe to recreate; only `local_config/` can't be regenerated |

Full guide: `docs/init.md`. Runtime layout contract: `.data.template/README.md`.

## Verification

After onboarding completes, verify the setup:

```bash
python skills/axiara-onboarding/scripts/verify_setup.py
```

This checks:
- ✓ `.data/` directory structure is correct
- ✓ Configuration file exists with required sections
- ✓ Store sync status (if git mode)
- ✓ Manifest initialization

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
- **Initialization guide**: `docs/init.md`
- **Data directory contract**: `.data.template/README.md`
