#!/usr/bin/env bash
#
# init-data.sh — bootstrap .data/ and write local config (agent-driven setup)
#
# The onboarding Q&A is conducted by the Agent in the user's chosen language
# (per docs/init.md). This script only performs the actual setup:
#   1. create the five runtime dirs under .data/
#   2. write / update .data/local_config/config from CLI flags (or defaults)
#   3. sync the team data repo into .data/store/ if a URL is set
#
# It NEVER prompts interactively, so it is safe for agents and CI.
#
# Usage (all flags optional; omitted values keep existing config or defaults):
#   bash scripts/init-data.sh \
#       [--language zh-CN] \
#       [--sync-mode none|git|sql] \
#       [--backend sqlite|csv|mysql|mariadb|postgresql] \
#       [--db-dsn postgresql://user:pass@host:5432/db] \
#       [--data-source local_file|team_repo|none] \
#       [--repo-url https://github.com/org/axiara-data.git] \
#       [--default-currency CNY] \
#       [--user-id AX-abcd-1234] \
#       [--branch-strategy A|B] \
#       [--enable-branch-archive true|false]
#
# With no flags: creates dirs; writes a default config only if none exists
# (existing config is never touched). With flags: writes config (backing up
# the previous one to config.bak first).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$ROOT/.data"
TEMPLATE_DIR="$ROOT/.data.template"
CONFIG_FILE="$DATA_DIR/local_config/config"

cfg_get() {
  sed -n "s/^[[:space:]]*${1}[[:space:]]*=[[:space:]]*//p" "$CONFIG_FILE" | head -1
}

# defaults
LANG_CFG=en; SYNC_MODE=none; BACKEND=sqlite; DATA_SOURCE=none
REPO_URL=""; REPO_BRANCH=main; GIT_USER=""; GIT_EMAIL=""; DB_DSN=""; DEFAULT_CURRENCY=""
USER_ID=""; BRANCH_STRATEGY="A"; ENABLE_BRANCH_ARCHIVE="false"
HAS_ARGS=0

# Language to currency mapping (suggested defaults)
LANG_TO_CURRENCY() {
  case "$1" in
    zh-CN) echo "CNY" ;;
    zh-TW) echo "TWD" ;;
    ja)    echo "JPY" ;;
    ko)    echo "KRW" ;;
    de|fr|es) echo "EUR" ;;
    pt-BR) echo "BRL" ;;
    ru)    echo "RUB" ;;
    en|*)  echo "USD" ;;
  esac
}

# parse flags
while [ $# -gt 0 ]; do
  case "$1" in
    --language)       LANG_CFG="$2"; HAS_ARGS=1; shift 2 ;;
    --sync-mode)      SYNC_MODE="$2"; HAS_ARGS=1; shift 2 ;;
    --backend)        BACKEND="$2"; HAS_ARGS=1; shift 2 ;;
    --db-dsn)         DB_DSN="$2"; HAS_ARGS=1; shift 2 ;;
    --data-source)    DATA_SOURCE="$2"; HAS_ARGS=1; shift 2 ;;
    --repo-url)       REPO_URL="$2"; HAS_ARGS=1; shift 2 ;;
    --default-currency) DEFAULT_CURRENCY="$2"; HAS_ARGS=1; shift 2 ;;
    --user-id)        USER_ID="$2"; HAS_ARGS=1; shift 2 ;;
    --branch-strategy) BRANCH_STRATEGY="$2"; HAS_ARGS=1; shift 2 ;;
    --enable-branch-archive) ENABLE_BRANCH_ARCHIVE="$2"; HAS_ARGS=1; shift 2 ;;
    --non-interactive) : ;;  # no-op — the script is always non-interactive
    *) echo "error: unknown option: $1 (see header for usage)"; exit 1 ;;
  esac
done

# load existing values as fallback defaults
if [ -f "$CONFIG_FILE" ]; then
  REPO_URL="${REPO_URL:-$(cfg_get url)}"; REPO_BRANCH="$(cfg_get branch)"; REPO_BRANCH="${REPO_BRANCH:-main}"
  GIT_USER="$(cfg_get user_name)"; GIT_EMAIL="$(cfg_get user_email)"
  LANG_CFG="${LANG_CFG:-$(cfg_get language)}"; LANG_CFG="${LANG_CFG:-en}"
  SYNC_MODE="${SYNC_MODE:-$(cfg_get sync_mode)}"; SYNC_MODE="${SYNC_MODE:-none}"
  BACKEND="${BACKEND:-$(cfg_get backend)}"; BACKEND="${BACKEND:-sqlite}"
  DATA_SOURCE="${DATA_SOURCE:-$(cfg_get data_source)}"; DATA_SOURCE="${DATA_SOURCE:-none}"
  DB_DSN="${DB_DSN:-$(cfg_get db_dsn)}"
  DEFAULT_CURRENCY="${DEFAULT_CURRENCY:-$(cfg_get default_currency)}"
  USER_ID="${USER_ID:-$(cfg_get user_id)}"
  BRANCH_STRATEGY="${BRANCH_STRATEGY:-$(cfg_get branch_strategy)}"; BRANCH_STRATEGY="${BRANCH_STRATEGY:-A}"
  ENABLE_BRANCH_ARCHIVE="${ENABLE_BRANCH_ARCHIVE:-$(cfg_get enable_branch_archive)}"; ENABLE_BRANCH_ARCHIVE="${ENABLE_BRANCH_ARCHIVE:-false}"
fi

# Infer default currency from language if not specified
if [ -z "$DEFAULT_CURRENCY" ]; then
  DEFAULT_CURRENCY=$(LANG_TO_CURRENCY "$LANG_CFG")
  echo "→ inferred default currency: $DEFAULT_CURRENCY (from language: $LANG_CFG)"
fi

# validate
case "$LANG_CFG" in
  en|zh-CN|zh-TW|ja|ko|de|fr|es|pt-BR|ru) ;;
  *) echo "error: invalid --language: $LANG_CFG"; exit 1 ;;
esac
case "$SYNC_MODE" in
  none|git|sql) ;;
  *) echo "error: invalid --sync-mode: $SYNC_MODE (none|git|sql)"; exit 1 ;;
esac
case "$BACKEND" in
  sqlite|csv|mysql|mariadb|postgresql) ;;
  *) echo "error: invalid --backend: $BACKEND"; exit 1 ;;
esac
case "$DATA_SOURCE" in
  local_file|team_repo|none) ;;
  *) echo "error: invalid --data-source: $DATA_SOURCE"; exit 1 ;;
esac
case "$BRANCH_STRATEGY" in
  A|B) ;;
  *) echo "error: invalid --branch-strategy: $BRANCH_STRATEGY (A|B)"; exit 1 ;;
esac
case "$ENABLE_BRANCH_ARCHIVE" in
  true|false) ;;
  *) echo "error: invalid --enable-branch-archive: $ENABLE_BRANCH_ARCHIVE (true|false)"; exit 1 ;;
esac
[ "$SYNC_MODE" = "sql" ] && [ -z "$DB_DSN" ] && echo "warning: sync_mode=sql but no --db-dsn provided"

mkdir -p "$DATA_DIR"/store "$DATA_DIR"/cache "$DATA_DIR"/ledger "$DATA_DIR"/db_dump "$DATA_DIR"/local_config

export_yaml_config() {
  cat > "$YAML_CONFIG_FILE" <<EOF
# Axiara workspace configuration (YAML format)
# Generated by scripts/init-data.sh on $(date +%Y-%m-%d)
# This is a YAML export of the INI config for better tool compatibility

data_repo:
  url: "${REPO_URL}"
  branch: "${REPO_BRANCH}"

git:
  user_name: "${GIT_USER}"
  user_email: "${GIT_EMAIL}"

app:
  language: "${LANG_CFG}"
  sync_mode: "${SYNC_MODE}"
  backend: "${BACKEND}"
  data_source: "${DATA_SOURCE}"
  default_currency: "${DEFAULT_CURRENCY}"
  user_id: "${USER_ID}"
  branch_strategy: "${BRANCH_STRATEGY}"
  enable_branch_archive: "${ENABLE_BRANCH_ARCHIVE}"

storage:
  db_dsn: "${DB_DSN}"
EOF
}

write_config() {
  {
    echo "# Axiara local configuration"
    echo "# Generated by scripts/init-data.sh on $(date +%Y-%m-%d)"
    echo "# Private per-user settings. Do not commit, do not sync."
    echo ""
    echo "[data_repo]"
    echo "# Team shared data repository, synced by the Agent into .data/store/ (git)."
    echo "url = ${REPO_URL}"
    echo "branch = ${REPO_BRANCH}"
    echo ""
    echo "[git]"
    echo "# Identity used for commits inside this workspace"
    echo "user_name = ${GIT_USER}"
    echo "user_email = ${GIT_EMAIL}"
    echo ""
    echo "[app]"
    echo "# Interface/output language: en | zh-CN | zh-TW | ja | ko | de | fr | es | pt-BR | ru"
    echo "language = ${LANG_CFG}"
    echo "# Sync mode: none (personal) | git (text+Git, CSV) | sql (SQL server)"
    echo "sync_mode = ${SYNC_MODE}"
    echo "# Backend: sqlite | csv | mysql | mariadb | postgresql"
    echo "backend = ${BACKEND}"
    echo "# Data source: local_file | team_repo | none"
    echo "data_source = ${DATA_SOURCE}"
    echo "# Default currency (ISO 4217): CNY | USD | EUR | JPY | GBP | KRW | etc."
    echo "default_currency = ${DEFAULT_CURRENCY}"
    echo "# User ID (stable identifier for learn sync): AX-xxxx-yyyy"
    echo "user_id = ${USER_ID}"
    echo "# Branch strategy: A (per-user branches, default) | B (single upload branch)"
    echo "branch_strategy = ${BRANCH_STRATEGY}"
    echo "# Enable automatic archiving of inactive user branches"
    echo "enable_branch_archive = ${ENABLE_BRANCH_ARCHIVE}"
    echo ""
    echo "[storage]"
    echo "# Connection string — only used when sync_mode = sql"
    echo "db_dsn = ${DB_DSN}"
  } > "$CONFIG_FILE"
}

if [ "$HAS_ARGS" = "1" ] || [ ! -f "$CONFIG_FILE" ]; then
  if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$CONFIG_FILE.bak"
    echo "→ previous config backed up: $CONFIG_FILE.bak"
  fi
  write_config
  echo "→ wrote $CONFIG_FILE"
  
  # Export YAML config
  YAML_CONFIG_FILE="$DATA_DIR/local_config/workspace.config.yaml"
  export_yaml_config
  echo "→ exported $YAML_CONFIG_FILE"
else
  echo "→ config exists and no flags passed; leaving it untouched"
fi

if [ -n "$REPO_URL" ]; then
  if [ -d "$DATA_DIR/store/.git" ]; then
    if ! git -C "$DATA_DIR/store" pull --ff-only; then
      echo "→ warning: store/ pull failed — check network/credentials, retry later"
    else
      echo "→ updated $DATA_DIR/store"
    fi
  else
    if ! git clone --depth 1 "$REPO_URL" "$DATA_DIR/store"; then
      echo "→ warning: store/ clone failed — check network/credentials and repo-url"
    else
      echo "→ cloned team data repo into $DATA_DIR/store"
    fi
  fi
else
  echo "→ no data repo URL; store/ stays empty"
fi

echo "✔ .data/ ready: store cache ledger db_dump local_config"
case "$DATA_SOURCE" in
  local_file) echo "   Next: import your price list — template at docs/templates/price-list.csv.example (see docs/init.md)" ;;
  team_repo)  echo "   Next: team data synced into store/ — see docs/init.md" ;;
  none)       echo "   Next: start empty — docs/init.md explains how to fetch data later" ;;
esac
