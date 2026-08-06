# Axiara Configuration Schema

Configuration file: `.data/local_config/config`

## Structure

The configuration file uses INI format with the following sections:

### [data_repo]

Data repository settings for git-synced store.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | none | Git repository URL for team data sync |
| `branch` | string | main | Git branch to sync |
| `auto_sync` | boolean | false | Auto-pull on startup (push is manual) |

**Example:**
```ini
[data_repo]
url = https://github.com/team/axiara-data.git
branch = main
auto_sync = false
```

### [git]

Git user configuration for commits.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `user_name` | string | none | Git committer name |
| `user_email` | string | none | Git committer email |

**Example:**
```ini
[git]
user_name = Your Name
user_email = your@email.com
```

### [app]

Application settings.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `language` | string | en | Output language for quotations, ledgers, documents |
| `sync_mode` | string | none | Sync mode: `none`, `git`, or `sql` |
| `backend` | string | sqlite | Data format: `sqlite`, `csv`, `mysql`, `mariadb`, `postgresql` |

**Supported languages:** `en`, `zh-CN`, `zh-TW`, `ja`, `ko`, `de`, `fr`, `es`, `pt-BR`, `ru`

**Sync modes:**
- `none` - Personal mode, SQLite local storage
- `git` - Team mode, CSV files synced via git
- `sql` - Team mode, SQL server (MySQL/MariaDB/PostgreSQL)

**Example:**
```ini
[app]
language = zh-CN
sync_mode = git
backend = csv
```

### [storage]

Storage backend settings (for SQL modes).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `db_dsn` | string | none | Database connection string (SQL only) |

**Example DSN formats:**
- MySQL: `mysql://user:pass@host:3306/dbname`
- PostgreSQL: `postgresql://user:pass@host:5432/dbname`
- SQLite: `sqlite:///path/to/local.db` (local cache, always on)

**Example:**
```ini
[storage]
db_dsn = mysql://axiara:password@localhost:3306/axiara_db
```

## Complete Example

**Personal mode (SQLite):**
```ini
[app]
language = en
sync_mode = none
backend = sqlite

[git]
user_name = Your Name
user_email = your@email.com
```

**Team mode (CSV + git):**
```ini
[data_repo]
url = https://github.com/team/axiara-data.git
branch = main
auto_sync = false

[git]
user_name = Your Name
user_email = your@email.com

[app]
language = zh-CN
sync_mode = git
backend = csv
```

**Team mode (SQL server):**
```ini
[git]
user_name = Your Name
user_email = your@email.com

[app]
language = en
sync_mode = sql
backend = mysql

[storage]
db_dsn = mysql://axiara:password@db.example.com:3306/axiara
```

## Validation

Run verification after setup:
```bash
python skills/axiara-onboarding/scripts/verify_setup.py
```

## See Also

- Initialization guide: `docs/init.md`
- Data directory contract: `.data.template/README.md`
- Business modes: `docs/business-modes.md`