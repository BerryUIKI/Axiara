# docs/init.md — First-time Setup, Data Guide & Data Integrity

How to bring a fresh clone of Axiara to a working state and decide where the data comes from. Read this when setting up a new workspace or after the runtime data directory went missing.

> **For the Agent:** this document is written in English on purpose (docs stay single-language). Conduct the onboarding Q&A **in the user's chosen language**, then run `scripts/init-data.sh` with the answers as flags (see "Setup flow" below). The user never needs to read this file.

## Why this is needed

`.data/` is the runtime data directory and it is gitignored, so it does **not** exist right after `git clone`. `scripts/init-data.sh` creates it and writes the private config. The script is **fully non-interactive** — the questions are asked by you (the Agent), in the user's language; the script only performs the setup.

## Storage & sync model (no servers required)

Ask the user **one question first: do you need team sync?** Everything else follows:

```
Need team sync?
├─ No (personal)  → SQLite (single-file database, zero config)
└─ Yes (team)
    ├─ 1. Text + Git  → CSV files synced via git into store/ (no server)
    └─ 2. SQL server  → MySQL / MariaDB / PostgreSQL (needs a connection string)
```

- **Personal** — SQLite is the store. Simple, single file, nothing to configure.
- **Team · text + Git** — CSV is the source of truth: users edit it in Excel, git syncs it (`store/`), and the Agent **automatically maintains a local SQLite cache** for fast queries (reads the cache instead of whole CSV files → saves tokens). The cache lives in `.data/cache/`, is rebuildable from CSV, and never enters git. No user choice needed.
- **Team · SQL server** — the server database is the source of truth; the Agent queries it directly. Needs a connection string (`postgresql://` or `mysql://`).

Data file format is **CSV by default** (Excel-editable, git-friendly). JSON/YAML are used internally for Agent-generated artifacts (rules, templates, learned output) — the user never chooses a format.

## Setup flow (agent-driven)

1. **Language** — ask the user which language they want Axiara to output (quotations, ledgers, documents). Options: `en zh-CN zh-TW ja ko de fr es pt-BR ru`.
2. **Storage & sync** — ask "do you need team sync?" (see decision tree above). If SQL server: also ask which (MySQL / MariaDB / PostgreSQL) and the connection string.
3. **Data source** — ask where their data comes from: local files (price lists to import) / team repo (enter URL) / no data yet.
4. **Dev environment (optional)** — ask: *"Do you want to set up a Python environment for running Axiara yourself (REST API / CLI / tests), or will you use Axiara through me (your AI agent) only?"*
   - **Agent-only (recommended, zero-setup)** — no `.venv` needed; the Agent handles everything. This is the default.
   - **With dev environment** — the Agent runs `uv sync` so the user can later start the REST API (`uv run uvicorn axiara.api.main:app`), the CLI (`uv run axiara`), or run tests (`uv run pytest`).
   - What the user gives up without it: they cannot start the REST API / CLI / tests by themselves; crawler fetching and Excel quote generation are done by the Agent on demand. Core Agent-workspace usage is unaffected either way.
5. Run the script with the answers:

```bash
bash scripts/init-data.sh \
  --language zh-CN \
  --sync-mode git --backend csv \
  --data-source team_repo --repo-url https://github.com/your-org/axiara-data.git
```

Valid values: `--sync-mode none|git|sql` · `--backend sqlite|csv|mysql|mariadb|postgresql` · `--data-source local_file|team_repo|none` · `--db-dsn <connection string>` (SQL only). Omitted flags keep the existing config (or defaults on first run). Re-running with flags backs up the previous config to `config.bak` first; running with **no flags** never touches an existing config (safe for agents/CI).

## Data guide (where the data comes from)

### A. The user has local data (Excel / CSV price lists)

1. Give them the template: `docs/templates/price-list.csv.example` → they fill it with their official prices (name, spec, unit, unit_price, currency, effective_date, note).
2. Import it: *"import price-list.csv into data/main/"* — it becomes the **official baseline** (human-edit only, versioned).
3. Historical invoices / order sheets can be imported too — the Agent learns from them into `data/learn/` (never overwrites the official baseline).
4. To share with the team: commit the files into the team repo (`store/`) — see B.

### B. The user has a team repo (`axiara-data`)

Set `--repo-url` during setup (or `[data_repo] url` in `config`). The Agent clones it into `.data/store/` and keeps it in sync (`git pull --ff-only` on each init). Data files live in the repo as CSV, versioned and multi-user.

### C. No data yet

Nothing is blocked — start empty and fetch data later:

- **Market prices**: fetch current market prices (crawled into `data/market/`). Product rule: crawled data needs **confirmation before entering** the baseline — it can never silently overwrite official prices.
- **Learn over time**: as quotations are approved and mistakes corrected, the Agent learns costing patterns into `data/learn/`.
- **Join a team later**: set `[data_repo] url` in `config` and re-run the script.

## Data integrity (anti-tampering)

Users can physically edit or delete their own files — you cannot prevent that. What you CAN do is **detect, recover, audit**:

1. **Detect** — maintain a SHA-256 manifest of the official-baseline files (store it in `db_dump/`, not the wipeable `cache/`). Compare before every operation / at startup; a deleted file is detected because the manifest entry has no file. In team mode also check `git status` (uncommitted changes = files were touched).
2. **Recover** — team mode: `git log` + restore from any historical version. Personal mode: take periodic snapshots of the official baseline into `db_dump/`; the SQLite cache is the last-resort backup (re-exportable).
3. **Audit** — record every detected change event in `ledger/` (time, file, hash before/after); in team mode, git commit history is the audit trail — tampering cannot hide.

**On any unexpected change to the official baseline: do NOT silently continue.** Enter review mode (mode four): show the diff, ask "did you change this?", and only continue quoting after confirmation. Legitimate human edits keep working — they just go through versioned history.

## Private config (`local_config/config`)

Written by the script (or from `.data.template/local_config.example`). Private to each machine — never commit, never share.

```ini
[data_repo]
url =                    # team data repo (git); empty = skip auto-pull
branch = main

[git]
user_name =              # identity used for commits
user_email =

[app]
language = en            # en | zh-CN | zh-TW | ja | ko | de | fr | es | pt-BR | ru
sync_mode = none         # none (personal) | git (text+Git, CSV) | sql (SQL server)
backend = sqlite         # sqlite | csv | mysql | mariadb | postgresql
data_source = none       # local_file | team_repo | none
dev_env = false          # true = user set up .venv (can run REST API/CLI/tests); false = agent-only

[storage]
db_dsn =                 # only when sync_mode = sql (postgresql:// or mysql://)
```

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| `store/` is empty | `data_repo.url` not set — pass `--repo-url` and re-run |
| `store/` clone/pull failed (warning, not fatal) | Network / credentials / URL — fix and re-run; setup itself already succeeded |
| SQL connection fails | Wrong `--db-dsn` — check host/port/credentials and re-run |
| Official baseline changed unexpectedly | Anti-tampering flow: report the diff, confirm with the user, restore from git/snapshot if needed |
| Config "lost" edits | Re-running with flags backs up to `config.bak` first; no-flags runs never touch it |
| `.data/` partly deleted | Safe to recreate: only `local_config/` cannot be regenerated automatically |
| Binary / big files in git | Keep them out of `store/` — git is for text data files only |

## When to re-run

- Fresh clone
- `.data/` was wiped or corrupted (back up `local_config/` first — it is not regenerated)
- The user wants to change language / storage & sync / data source
