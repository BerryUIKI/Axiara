# .data/ — Axiara Runtime Data Layout

> This directory is the **template** for `.data/`. It is tracked in git so every clone
> ships the structure; `.data/` itself is gitignored and created at runtime.
> Bootstrap: `bash scripts/init-data.sh` (the app also auto-creates missing dirs on first start).
> Full setup & troubleshooting: `docs/init.md`.

| Directory       | Purpose                                                              | Lifecycle            | Git |
| --------------- | -------------------------------------------------------------------- | -------------------- | --- |
| `store/`        | Team shared data — Agent keeps in sync with the `axiara-data` repo (incl. `learn_shared/` public rules + `learn_inbox/` uploads, see `docs/learn-sync-text.md`)   | Persistent           | Never (cloned from remote) |
| `cache/`        | Temp caches, logs, intermediate computation outputs                  | Safe to wipe anytime | Never |
| `ledger/`       | Local ledgers / journals                                             | Persistent           | Never |
| `db_dump/`      | Database backups (`pg_dump` / `mongodump` / SQLite file copies)      | Persistent, rotate   | Never |
| `local_config/` | Per-user private config (`config`, from `local_config.example`)      | Persistent           | Never |

## Notes

- `data/` (no dot) is the **business data layer** (`main_db` / `learn_db` / `market_db`); `.data/` is the **runtime / ops layer**. Do not confuse them.
- `local_config/config` is created once from `local_config.example`; edit it, never delete it.
- To share ledgers across the team, move them into `store/` instead of keeping them in `ledger/`.
